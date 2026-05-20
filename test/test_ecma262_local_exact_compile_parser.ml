let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-local-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-local-exact-plan.tsv is missing; run \
           tools/build_ecma262_regexp_local_exact_plan.py"
      else climb parent
  in
  climb cwd

let path segments = List.fold_left Filename.concat (repo_root ()) segments

let strip_trailing_cr value =
  let length = String.length value in
  if length > 0 && value.[length - 1] = '\r' then String.sub value 0 (length - 1)
  else value

let split_tsv_line line = line |> strip_trailing_cr |> String.split_on_char '\t'

let pad_to width fields =
  let rec loop fields =
    if List.length fields >= width then fields else loop (fields @ [ "" ])
  in
  loop fields

let read_tsv rel =
  let file = path rel in
  let ic = open_in file in
  Fun.protect
    ~finally:(fun () -> close_in_noerr ic)
    (fun () ->
      let header = split_tsv_line (input_line ic) in
      let width = List.length header in
      let rec rows acc =
        match input_line ic with
        | line ->
            let fields = split_tsv_line line |> pad_to width in
            let row = List.combine header fields in
            rows (row :: acc)
        | exception End_of_file -> List.rev acc
      in
      rows [])

let field name row =
  match List.assoc_opt name row with
  | Some value -> value
  | None -> Alcotest.failf "missing TSV field %s" name

let plan_rows () = read_tsv [ "cache"; "ecma262-regexp-local-exact-plan.tsv" ]

let count_by field_name rows =
  let counts = Hashtbl.create 16 in
  List.iter
    (fun row ->
      let key = field field_name row in
      let count = Option.value (Hashtbl.find_opt counts key) ~default:0 in
      Hashtbl.replace counts key (count + 1))
    rows;
  counts

let check_count counts key expected =
  Alcotest.(check int)
    key expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let compile_row row =
  let pattern = field "planned_pattern" row in
  let planned_flags = field "planned_flags" row in
  let compile_with flags = Ecma_regex.compile ~flags pattern in
  if planned_flags = "" then Ecma_regex.compile pattern
  else
    match Ecma_regex.flags_of_string planned_flags with
    | Error msg ->
        Error
          (Printf.sprintf "planned flags should parse: flags=%S error=%s"
             planned_flags msg)
    | Ok flags -> compile_with flags

let failure_line row msg =
  Printf.sprintf
    "plan_id=%s requirement=%s family=%s layer=%s pattern=%S flags=%S error=%s"
    (field "plan_id" row)
    (field "requirement_id" row)
    (field "local_case_family" row)
    (field "executable_layer" row)
    (field "planned_pattern" row)
    (field "planned_flags" row)
    msg

let summarize_failures failures =
  let family_counts = Hashtbl.create 16 in
  List.iter
    (fun (row, _msg) ->
      let family = field "local_case_family" row in
      let count =
        Option.value (Hashtbl.find_opt family_counts family) ~default:0
      in
      Hashtbl.replace family_counts family (count + 1))
    failures;
  let family_summary =
    family_counts |> Hashtbl.to_seq |> List.of_seq
    |> List.sort (fun (left, _) (right, _) -> String.compare left right)
    |> List.map (fun (family, count) -> Printf.sprintf "%s=%d" family count)
    |> String.concat ", "
  in
  let examples =
    failures |> List.to_seq |> Seq.take 20 |> List.of_seq
    |> List.map (fun (row, msg) -> failure_line row msg)
    |> String.concat "\n"
  in
  Printf.sprintf
    "local exact compile/parser failures: total=%d by_family={%s}\n%s"
    (List.length failures) family_summary examples

let executable_rows rows =
  List.filter
    (fun row ->
      field "expected_behavior" row = "compile_ok"
      && field "plan_state" row = "planned_not_executable"
      && field "coverage_credit" row = "none_local_exact_planned")
    rows

let test_local_exact_compile_parser_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "local exact plan rows" 319 (List.length rows);
  let executable = executable_rows rows in
  Alcotest.(check int) "executable planned rows" 319 (List.length executable);
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "compile" 17;
  check_count layer_counts "parser" 302;
  let family_counts = count_by "local_case_family" rows in
  check_count family_counts "compile_literal_validity" 1;
  check_count family_counts "compile_surface_exact" 16;
  check_count family_counts "parser_capture_local_exact" 27;
  check_count family_counts "parser_character_class_local_exact" 4;
  check_count family_counts "parser_character_escape_local_exact" 79;
  check_count family_counts "parser_modifiers_local_exact" 15;
  check_count family_counts "parser_unicode_property_local_exact" 131;
  check_count family_counts "parser_unicode_sets_local_exact" 46

let test_local_exact_compile_parser_cases () =
  let failures =
    plan_rows () |> executable_rows
    |> List.filter_map (fun row ->
        match compile_row row with Ok _ -> None | Error msg -> Some (row, msg))
  in
  match failures with
  | [] -> ()
  | failures -> Alcotest.fail (summarize_failures failures)

let () =
  Alcotest.run "ecma262-local-exact-compile-parser"
    [
      ( "manifest",
        [
          Alcotest.test_case "local exact executable plan invariants" `Quick
            test_local_exact_compile_parser_manifest;
        ] );
      ( "compile",
        [
          Alcotest.test_case "local exact planned compile/parser cases" `Quick
            test_local_exact_compile_parser_cases;
        ] );
    ]
