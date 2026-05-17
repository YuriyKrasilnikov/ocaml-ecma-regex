let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/test262-regexp-negative-syntax-cases.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/test262-regexp-negative-syntax-cases.tsv is missing; run \
           tools/extract_test262_regexp_negative_syntax.py"
      else climb parent
  in
  climb cwd

let path segments =
  List.fold_left Filename.concat (repo_root ()) segments

let strip_trailing_cr value =
  let length = String.length value in
  if length > 0 && value.[length - 1] = '\r' then
    String.sub value 0 (length - 1)
  else value

let split_tsv_line line =
  line
  |> strip_trailing_cr
  |> String.split_on_char '\t'

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

let negative_rows () =
  read_tsv [ "cache"; "test262-regexp-negative-syntax-cases.tsv" ]

let source_exists source_path =
  Sys.file_exists (path [ "external"; "test262"; source_path ])

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
    key
    expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let test_negative_manifest () =
  let rows = negative_rows () in
  Alcotest.(check int) "negative compile cases" 410 (List.length rows);
  let extractor_counts = count_by "extractor" rows in
  check_count extractor_counts "assert_throws_syntax_error" 169;
  check_count extractor_counts "legacy_try_test262error" 63;
  check_count extractor_counts "metadata_parse_negative_literal" 178;
  let kind_counts = count_by "source_kind" rows in
  check_count kind_counts "literal_parse_negative" 178;
  check_count kind_counts "regexp_compile_method_string" 8;
  check_count kind_counts "regexp_constructor_string" 93;
  check_count kind_counts "regexp_function_string" 131;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "expected behavior"
         "compile_error"
         (field "expected_behavior" row);
       if field "pattern" row = "" && field "flags" row = "" then
         Alcotest.failf "%s:%s: empty negative case"
           (field "source_path" row)
           (field "line" row);
       if not (source_exists (field "source_path" row)) then
         Alcotest.failf "%s: missing test262 source" (field "source_path" row))
    rows

let check_negative_case index total row =
  let pattern = field "pattern" row in
  let flags_source = field "flags" row in
  let result =
    if flags_source = "" then Ecma_regex.compile pattern
    else
      match Ecma_regex.flags_of_string flags_source with
      | Error _ -> Error "invalid flags"
      | Ok flags -> Ecma_regex.compile ~flags pattern
  in
  match result with
  | Error _ -> ()
  | Ok _ ->
    Alcotest.failf
      "test262 negative syntax case unexpectedly compiled (%d/%d): %s:%s \
       kind=%s extractor=%s raw=%S pattern=%S flags=%S"
      (index + 1) total
      (field "source_path" row)
      (field "line" row)
      (field "source_kind" row)
      (field "extractor" row)
      (field "raw" row)
      pattern flags_source

let test_negative_cases_reject () =
  let rows = negative_rows () in
  List.iteri
    (fun index row -> check_negative_case index (List.length rows) row)
    rows

let () =
  Alcotest.run "test262-negative-syntax" [
    ("manifest", [
      Alcotest.test_case "generated negative syntax manifest" `Quick
        test_negative_manifest;
    ]);
    ("compile", [
      Alcotest.test_case "negative syntax cases reject" `Quick
        test_negative_cases_reject;
    ]);
  ]
