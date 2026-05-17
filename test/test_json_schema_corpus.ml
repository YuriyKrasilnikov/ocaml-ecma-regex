type schema_case = {
  description : string;
  schema : Yojson.Safe.t;
  tests : (string * Yojson.Safe.t * bool) list;
}

let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate = Filename.concat dir "external/json-schema-test-suite" in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail "external/json-schema-test-suite is missing; run tools/fetch_json_schema_test_suite.py"
      else climb parent
  in
  climb cwd

let repo_path rel =
  Filename.concat (repo_root ()) rel

let strip_trailing_cr value =
  let length = String.length value in
  if length > 0 && value.[length - 1] = '\r' then
    String.sub value 0 (length - 1)
  else value

let split_tsv_line line =
  line
  |> strip_trailing_cr
  |> String.split_on_char '\t'

let read_manifest () =
  let file = repo_path "test/json_schema_corpus_files.tsv" in
  let ic = open_in file in
  Fun.protect
    ~finally:(fun () -> close_in_noerr ic)
    (fun () ->
       let header = split_tsv_line (input_line ic) in
       if header <> [ "suite"; "rel_path" ] then
         Alcotest.fail "invalid JSON Schema corpus manifest header";
       let rec rows acc =
         match input_line ic with
         | line ->
           (match split_tsv_line line with
            | [ suite; rel_path ] when suite <> "" && rel_path <> "" ->
              rows ((suite, rel_path) :: acc)
            | [ "" ] -> rows acc
            | _ -> Alcotest.failf "invalid JSON Schema corpus manifest line: %s" line)
         | exception End_of_file -> List.rev acc
       in
       rows [])

let member name = function
  | `Assoc fields -> List.assoc_opt name fields
  | _ -> None

let string_member name json =
  match member name json with
  | Some (`String s) -> s
  | _ -> Alcotest.failf "missing string field %s" name

let bool_member name json =
  match member name json with
  | Some (`Bool b) -> b
  | _ -> Alcotest.failf "missing bool field %s" name

let list_member name json =
  match member name json with
  | Some (`List xs) -> xs
  | _ -> Alcotest.failf "missing list field %s" name

let read_cases rel =
  let json = Yojson.Safe.from_file (repo_path rel) in
  match json with
  | `List groups ->
    List.map (fun group ->
      {
        description = string_member "description" group;
        schema = (match member "schema" group with Some s -> s | None -> Alcotest.fail "missing schema");
        tests =
          list_member "tests" group
          |> List.map (fun test ->
            let description = string_member "description" test in
            let data = match member "data" test with Some v -> v | None -> Alcotest.fail "missing data" in
            let valid = bool_member "valid" test in
            (description, data, valid));
      })
      groups
  | _ -> Alcotest.fail "expected top-level JSON array"

let integer = function
  | `Int _ | `Intlit _ -> true
  | _ -> false

let number = function
  | `Int _ | `Intlit _ | `Float _ -> true
  | _ -> false

let numeric_value = function
  | `Int n -> Some (float_of_int n)
  | `Intlit n -> (try Some (float_of_string n) with Failure _ -> None)
  | `Float n -> Some n
  | _ -> None

let check_json_type expected value =
  match expected, value with
  | "null", `Null -> true
  | "boolean", `Bool _ -> true
  | "object", `Assoc _ -> true
  | "array", `List _ -> true
  | "number", value -> number value
  | "integer", value -> integer value
  | "string", `String _ -> true
  | _ -> false

let check_maximum limit value =
  match numeric_value limit, numeric_value value with
  | Some limit, Some value -> value <= limit
  | Some _, None -> true
  | None, _ -> Alcotest.fail "unsupported non-numeric maximum in JSON Schema corpus"

let json_schema_regex_flags =
  Ecma_regex.flags ~unicode:true ()

let compile_json_schema_regex pattern =
  Ecma_regex.compile ~flags:json_schema_regex_flags pattern

let compile_pattern_properties pattern_properties =
  List.map
    (fun (pattern, subschema) ->
       match compile_json_schema_regex pattern with
       | Ok re -> (re, subschema)
       | Error msg -> Alcotest.failf "patternProperties compile failed: %s" msg)
    pattern_properties

let property_matches_pattern_properties compiled name =
  List.exists (fun (re, _subschema) -> Ecma_regex.search re name) compiled

let validate_pattern pattern value =
  match compile_json_schema_regex pattern with
  | Error msg -> Alcotest.failf "pattern compile failed: %s" msg
  | Ok re ->
    (match value with
     | `String s -> Ecma_regex.search re s
     | _ -> true)

let rec validate_schema schema value =
  match schema with
  | `Bool allowed -> allowed
  | `Assoc fields ->
    let compiled_pattern_properties =
      match List.assoc_opt "patternProperties" fields with
      | Some (`Assoc pattern_properties) ->
        compile_pattern_properties pattern_properties
      | Some _ ->
        Alcotest.fail "unsupported non-object patternProperties in JSON Schema corpus"
      | None -> []
    in
    let type_valid =
      match List.assoc_opt "type" fields with
      | Some (`String expected) -> check_json_type expected value
      | Some _ -> Alcotest.fail "unsupported non-string type in JSON Schema corpus"
      | None -> true
    in
    let maximum_valid =
      match List.assoc_opt "maximum" fields with
      | Some limit -> check_maximum limit value
      | None -> true
    in
    let pattern_valid =
      match List.assoc_opt "pattern" fields with
      | Some (`String pattern) -> validate_pattern pattern value
      | Some _ -> Alcotest.fail "unsupported non-string pattern in JSON Schema corpus"
      | None -> true
    in
    let pattern_properties_valid =
      match List.assoc_opt "patternProperties" fields with
      | Some (`Assoc _) ->
        validate_pattern_properties_compiled compiled_pattern_properties value
      | None -> true
      | Some _ -> assert false
    in
    let additional_properties_valid =
      match List.assoc_opt "additionalProperties" fields with
      | Some additional_schema ->
        validate_additional_properties additional_schema
          compiled_pattern_properties
          value
      | None -> true
    in
    type_valid
    && maximum_valid
    && pattern_valid
    && pattern_properties_valid
    && additional_properties_valid
  | _ -> Alcotest.fail "unsupported schema in JSON Schema corpus"

and validate_pattern_properties_compiled compiled value =
  match value with
  | `Assoc properties ->
    List.for_all
      (fun (name, property_value) ->
         List.for_all
           (fun (re, subschema) ->
              if Ecma_regex.search re name then
                validate_schema subschema property_value
              else true)
           compiled)
      properties
  | _ -> true

and validate_additional_properties additional_schema compiled value =
  match value with
  | `Assoc properties ->
    List.for_all
      (fun (name, property_value) ->
         if property_matches_pattern_properties compiled name then true
         else validate_schema additional_schema property_value)
      properties
  | _ -> true

let check_schema description schema tests =
  List.iter (fun (test_description, data, expected) ->
      let valid = validate_schema schema data in
      Alcotest.(check bool)
        (description ^ " / " ^ test_description)
        expected valid)
    tests

let check_format_regex description tests =
  List.iter (fun (test_description, data, expected) ->
    let valid =
      match data with
      | `String pattern ->
        (match compile_json_schema_regex pattern with
         | Ok _ -> true
         | Error _ -> false)
      | _ -> true
    in
    Alcotest.(check bool)
      (description ^ " / " ^ test_description)
      expected valid)
    tests

let check_case { description; schema; tests } =
  match schema with
  | `Assoc fields ->
    (match List.assoc_opt "pattern" fields with
     | Some (`String _) -> check_schema description schema tests
     | _ ->
       (match List.assoc_opt "patternProperties" fields with
        | Some (`Assoc pattern_properties) ->
          ignore pattern_properties;
          check_schema description schema tests
        | _ ->
          (match List.assoc_opt "format" fields with
           | Some (`String "regex") -> check_format_regex description tests
           | _ -> Alcotest.failf "%s: unsupported schema shape" description)))
  | _ -> Alcotest.failf "%s: unsupported schema" description

let suite rel =
  read_cases rel
  |> List.map (fun case ->
    Alcotest.test_case case.description `Quick (fun () -> check_case case))

let () =
  Alcotest.run "json-schema-corpus"
    (List.map (fun (name, rel) -> (name, suite rel)) (read_manifest ()))
