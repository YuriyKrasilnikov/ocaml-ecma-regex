let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-compile-parser-test-selection.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-compile-parser-test-selection.tsv is missing; \
           run tools/map_ecma262_compile_parser_candidates.py"
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

let selection_rows () =
  read_tsv [ "cache"; "ecma262-regexp-compile-parser-test-selection.tsv" ]

let source_exists selected_source =
  match String.split_on_char ':' selected_source with
  | source_path :: _ ->
      Sys.file_exists (path [ "external"; "test262"; source_path ])
  | [] -> false

let selected_compile_positive_rows rows =
  List.filter
    (fun row -> field "selection_state" row = "selected_compile_positive_case")
    rows

let negative_or_local_exact_rows rows =
  List.filter
    (fun row ->
      field "selection_state" row = "needs_negative_or_local_exact_case")
    rows

let split_csv value = List.filter (( <> ) "") (String.split_on_char ',' value)
let has_csv value expected = List.exists (( = ) expected) (split_csv value)

let unique_selected_cases rows =
  let seen = Hashtbl.create 32 in
  let rec loop acc = function
    | [] -> List.rev acc
    | row :: rest ->
        let case_id = field "selected_case_id" row in
        if Hashtbl.mem seen case_id then loop acc rest
        else begin
          Hashtbl.add seen case_id ();
          loop (row :: acc) rest
        end
  in
  loop [] rows

let test_selection_manifest () =
  let rows = selection_rows () in
  let selected = selected_compile_positive_rows rows in
  let negative = negative_or_local_exact_rows rows in
  let unique_cases = unique_selected_cases selected in
  Alcotest.(check int) "selection rows" 0 (List.length rows);
  Alcotest.(check int) "compile-positive selected rows" 0 (List.length selected);
  Alcotest.(check int) "negative/local-exact rows" 0 (List.length negative);
  Alcotest.(check int)
    "unique selected compile cases" 0 (List.length unique_cases);
  List.iter
    (fun row ->
      if field "selected_case_id" row = "" then
        Alcotest.failf "%s: selected_case_id is empty"
          (field "requirement_id" row);
      if field "selected_pattern" row = "" then
        Alcotest.failf "%s: selected_pattern is empty"
          (field "requirement_id" row);
      Alcotest.(check string)
        "selected expected behavior" "compile_ok"
        (field "selected_expected_behavior" row);
      Alcotest.(check string)
        "selection exactness" "selected_candidate_not_coverage"
        (field "selection_exactness" row);
      if not (source_exists (field "selected_case_source" row)) then
        Alcotest.failf "%s: missing selected test262 source %s"
          (field "requirement_id" row)
          (field "selected_case_source" row))
    selected;
  List.iter
    (fun row ->
      Alcotest.(check string)
        "negative/local expected behavior" "compile_error_or_local_exact_needed"
        (field "selected_expected_behavior" row);
      Alcotest.(check string)
        "negative/local exactness" "no_positive_exact_selection"
        (field "selection_exactness" row);
      Alcotest.(check string)
        "no selected case" ""
        (field "selected_case_id" row);
      if
        not
          (has_csv
             (field "candidate_selector_tags" row)
             "negative_syntax_needed")
      then
        Alcotest.failf "%s: negative/local row lacks negative selector"
          (field "requirement_id" row))
    negative

let compile_selected_case index total row =
  let pattern = field "selected_pattern" row in
  let selected_flags = field "selected_flags" row in
  let compile_result =
    if selected_flags = "" then Ecma_regex.compile pattern
    else
      match Ecma_regex.flags_of_string selected_flags with
      | Error msg ->
          Alcotest.failf
            "selected compile/parser case has flags that should parse (%d/%d): \
             requirement=%s case=%s source=%s flags=%S error=%s"
            (index + 1) total
            (field "requirement_id" row)
            (field "selected_case_id" row)
            (field "selected_case_source" row)
            selected_flags msg
      | Ok flags -> Ecma_regex.compile ~flags pattern
  in
  match compile_result with
  | Ok _ -> ()
  | Error msg ->
      Alcotest.failf
        "selected compile/parser case should compile (%d/%d): requirement=%s \
         case=%s source=%s raw=%S pattern=%S flags=%S error=%s"
        (index + 1) total
        (field "requirement_id" row)
        (field "selected_case_id" row)
        (field "selected_case_source" row)
        (field "selected_raw" row) pattern selected_flags msg

let test_selected_compile_positive_cases () =
  let selected =
    selection_rows () |> selected_compile_positive_rows |> unique_selected_cases
  in
  List.iteri
    (fun index row -> compile_selected_case index (List.length selected) row)
    selected

let () =
  Alcotest.run "ecma262-compile-parser-selection"
    [
      ( "manifest",
        [
          Alcotest.test_case "selection table invariants" `Quick
            test_selection_manifest;
        ] );
      ( "compile",
        [
          Alcotest.test_case "selected compile-positive cases" `Quick
            test_selected_compile_positive_cases;
        ] );
    ]
