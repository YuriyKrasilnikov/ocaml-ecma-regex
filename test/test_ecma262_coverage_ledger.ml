let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate = Filename.concat dir "cache/ecma262-regexp-coverage-ledger.tsv" in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-coverage-ledger.tsv is missing; run \
           tools/build_ecma262_regexp_coverage_ledger.py"
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

let ledger_rows () =
  read_tsv [ "cache"; "ecma262-regexp-coverage-ledger.tsv" ]

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

let source_exists case_source =
  if String.starts_with ~prefix:"external/ecma262/" case_source then
    match String.split_on_char '#' case_source with
    | source_path :: _ -> Sys.file_exists (path [ source_path ])
    | [] -> false
  else if String.starts_with ~prefix:"test/" case_source then
    match String.split_on_char ':' case_source with
    | source_path :: _ ->
      Sys.file_exists (path [ "external"; "test262"; source_path ])
    | [] -> false
  else false

let test_coverage_ledger_manifest () =
  let rows = ledger_rows () in
  Alcotest.(check int) "ledger rows" 2020 (List.length rows);
  let state_counts = count_by "ledger_state" rows in
  check_count state_counts "covered_by_compile_parser_exact" 21;
  check_count state_counts "covered_by_literal_lexer_exact" 3;
  check_count state_counts "covered_by_local_exact_compile_parser" 319;
  check_count state_counts "covered_by_match_engine_exact" 404;
  check_count state_counts "covered_by_exec_result_exact" 144;
  check_count state_counts "covered_by_spec_model_exact" 4;
  check_count state_counts "covered_by_test262_literal_lexer_exact" 25;
  check_count state_counts "covered_by_reused_candidate_exact_compile_parser" 224;
  check_count state_counts "covered_by_search_adapter" 16;
  check_count state_counts "covered_by_match_adapter" 25;
  check_count state_counts "covered_by_match_all_adapter" 16;
  check_count state_counts "covered_by_split_adapter" 52;
  check_count state_counts "covered_by_replace_adapter" 119;
  check_count state_counts "covered_by_escape_adapter" 32;
  check_count state_counts "covered_by_ucd_generated_tests" 366;
  check_count state_counts "non_applicable_with_reason" 248;
  check_count state_counts "not_direct_requirement" 2;
  check_count state_counts "open_requirement_to_test_mapping_missing" 0;
  check_count state_counts "open_test262_executable_extractor_missing" 0;
  check_count state_counts "open_ucd_generated_tests_missing" 0;
  let bucket_counts = count_by "ledger_bucket" rows in
  check_count bucket_counts "covered" 1770;
  check_count bucket_counts "closed_non_applicable" 248;
  check_count bucket_counts "closed_not_direct_requirement" 2;
  check_count bucket_counts "open_exact_mapping" 0;
  check_count bucket_counts "open_extractor" 0;
  check_count bucket_counts "open_generated_tests" 0;
  let gate_counts = count_by "release_gate" rows in
  check_count gate_counts "blocking" 0;
  check_count gate_counts "not_blocking" 2020;
  let owner_counts = count_by "coverage_owner" rows in
  check_count owner_counts "local_exact_tests" 1119;
  check_count owner_counts "ecma262_requirement_to_test_mapping" 0;
  check_count owner_counts "test262_executable_extractor" 25;
  check_count owner_counts "product_surface_adapter" 260;
  check_count owner_counts "product_surface_policy" 248;
  check_count owner_counts "ucd_generated_tests" 366;
  let credit_counts = count_by "exactness_coverage_credit" rows in
  check_count credit_counts "compile_parser_exact_requirement_credit" 21;
  check_count credit_counts "literal_lexer_exact_requirement_credit" 3;
  check_count credit_counts "local_exact_compile_parser_requirement_credit" 319;
  check_count credit_counts "match_engine_exact_requirement_credit" 404;
  check_count credit_counts "exec_result_exact_requirement_credit" 144;
  check_count credit_counts "spec_model_exact_requirement_credit" 4;
  check_count credit_counts "test262_literal_lexer_requirement_credit" 25;
  check_count credit_counts
    "reused_candidate_exact_compile_parser_requirement_credit" 224;
  check_count credit_counts "" 876;
  List.iter
    (fun row ->
       if String.starts_with ~prefix:"covered_by_" (field "ledger_state" row) then begin
         Alcotest.(check string)
           "covered bucket"
           "covered"
           (field "ledger_bucket" row);
         Alcotest.(check string)
           "covered release gate"
           "not_blocking"
           (field "release_gate" row);
         let expected_owner =
           match field "ledger_state" row with
           | "covered_by_test262_literal_lexer_exact" ->
             "test262_executable_extractor"
           | "covered_by_search_adapter"
           | "covered_by_match_adapter"
           | "covered_by_match_all_adapter"
           | "covered_by_split_adapter"
           | "covered_by_replace_adapter"
           | "covered_by_escape_adapter" ->
             "product_surface_adapter"
           | "covered_by_ucd_generated_tests" -> "ucd_generated_tests"
           | _ -> "local_exact_tests"
         in
         Alcotest.(check string)
           "covered owner"
           expected_owner
           (field "coverage_owner" row);
         Alcotest.(check string)
           "covered next artifact"
           "none"
           (field "ledger_next_artifact" row);
         if field "ledger_state" row = "covered_by_search_adapter" then begin
           Alcotest.(check string)
             "search adapter surface"
             "search_adapter"
             (field "surface_area" row);
           Alcotest.(check string)
             "search adapter artifact"
             "Ecma_regex.search_index"
             (field "ocaml_artifact" row);
           Alcotest.(check string)
             "search adapter exactness evidence"
             ""
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "search adapter exactness credit"
             ""
             (field "exactness_coverage_credit" row)
         end
         else if field "ledger_state" row = "covered_by_match_adapter" then begin
           Alcotest.(check string)
             "match adapter surface"
             "match_adapter"
             (field "surface_area" row);
           Alcotest.(check string)
             "match adapter artifact"
             "Ecma_regex.match_"
             (field "ocaml_artifact" row);
           Alcotest.(check string)
             "match adapter exactness evidence"
             ""
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "match adapter exactness credit"
             ""
             (field "exactness_coverage_credit" row)
         end
         else if field "ledger_state" row = "covered_by_match_all_adapter" then begin
           Alcotest.(check string)
             "matchAll adapter surface"
             "match_all_adapter"
             (field "surface_area" row);
           Alcotest.(check string)
             "matchAll adapter artifact"
             "Ecma_regex.match_all"
             (field "ocaml_artifact" row);
           Alcotest.(check string)
             "matchAll adapter exactness evidence"
             ""
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "matchAll adapter exactness credit"
             ""
             (field "exactness_coverage_credit" row)
         end
         else if field "ledger_state" row = "covered_by_split_adapter" then begin
           Alcotest.(check string)
             "split adapter surface"
             "split_adapter"
             (field "surface_area" row);
           Alcotest.(check string)
             "split adapter artifact"
             "Ecma_regex.split"
             (field "ocaml_artifact" row);
           Alcotest.(check string)
             "split adapter exactness evidence"
             ""
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "split adapter exactness credit"
             ""
             (field "exactness_coverage_credit" row)
         end
         else if field "ledger_state" row = "covered_by_replace_adapter" then begin
           Alcotest.(check string)
             "replace adapter surface"
             "replace_adapter"
             (field "surface_area" row);
           Alcotest.(check string)
             "replace adapter artifact"
             "Ecma_regex.replace"
             (field "ocaml_artifact" row);
           Alcotest.(check string)
             "replace adapter exactness evidence"
             ""
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "replace adapter exactness credit"
             ""
             (field "exactness_coverage_credit" row)
         end
         else if field "ledger_state" row = "covered_by_escape_adapter" then begin
           Alcotest.(check string)
             "escape adapter surface"
             "regexp_escape_adapter"
             (field "surface_area" row);
           Alcotest.(check string)
             "escape adapter artifact"
             "Ecma_regex.escape"
             (field "ocaml_artifact" row);
           Alcotest.(check string)
             "escape adapter exactness evidence"
             ""
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "escape adapter exactness credit"
             ""
             (field "exactness_coverage_credit" row)
         end
         else if field "ledger_state" row = "covered_by_ucd_generated_tests" then begin
           Alcotest.(check string)
             "UCD generated route"
             "needs_ucd_generated_tests"
             (field "route_status" row);
           Alcotest.(check string)
             "UCD generated primary next artifact"
             "tools/build_ucd_regexp_tests.py"
             (field "primary_next_artifact" row);
           Alcotest.(check string)
             "UCD generated exactness evidence"
             ""
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "UCD generated exactness credit"
             ""
             (field "exactness_coverage_credit" row)
         end
         else if field "ledger_state" row = "covered_by_compile_parser_exact" then begin
           Alcotest.(check string)
             "compile/parser exactness evidence kind"
             "compile_parser_exact_case"
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "compile/parser exactness credit"
             "compile_parser_exact_requirement_credit"
             (field "exactness_coverage_credit" row);
           if
             not
             (String.starts_with ~prefix:"compile-parser-exact:"
                  (field "exactness_case_id" row))
           then Alcotest.failf "%s: covered row must have compile-parser-exact case id"
               (field "requirement_id" row)
         end
         else if field "ledger_state" row = "covered_by_literal_lexer_exact" then begin
           Alcotest.(check string)
             "literal lexer exactness evidence kind"
             "literal_lexer_exact_case"
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "literal lexer exactness credit"
             "literal_lexer_exact_requirement_credit"
             (field "exactness_coverage_credit" row);
           if
             not
               (String.starts_with ~prefix:"literal-lexer-exact:"
                  (field "exactness_case_id" row))
           then Alcotest.failf
               "%s: covered row must have literal-lexer-exact case id"
               (field "requirement_id" row)
         end
         else if field "ledger_state" row = "covered_by_match_engine_exact" then begin
           Alcotest.(check string)
             "match-engine exactness credit"
             "match_engine_exact_requirement_credit"
             (field "exactness_coverage_credit" row);
           if field "exactness_evidence_kind" row = "match_engine_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-exact case id"
                 (field "requirement_id" row)
           end
          else if
            field "exactness_evidence_kind" row
            = "match_engine_atoms_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-atoms-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-atoms-exact case id"
                 (field "requirement_id" row)
           end
          else if
            field "exactness_evidence_kind" row
            = "match_engine_capture_exact_case"
          then begin
            if
              not
                (String.starts_with ~prefix:"match-engine-capture-exact:"
                   (field "exactness_case_id" row))
            then Alcotest.failf
                "%s: covered row must have match-engine-capture-exact case id"
                (field "requirement_id" row)
          end
          else if
            field "exactness_evidence_kind" row
            = "match_engine_unicode_sets_string_exact_case"
          then begin
            if
              not
                (String.starts_with
                   ~prefix:"match-engine-unicode-sets-string-exact:"
                   (field "exactness_case_id" row))
            then Alcotest.failf
                "%s: covered row must have match-engine-unicode-sets-string-exact case id"
                (field "requirement_id" row)
          end
          else if
            field "exactness_evidence_kind" row
            = "match_engine_unicode_sets_escape_string_exact_case"
          then begin
            if
              not
                (String.starts_with
                   ~prefix:"match-engine-unicode-sets-escape-string-exact:"
                   (field "exactness_case_id" row))
            then Alcotest.failf
                "%s: covered row must have match-engine-unicode-sets-escape-string-exact case id"
                (field "requirement_id" row)
          end
          else if
            field "exactness_evidence_kind" row
            = "match_engine_character_classes_exact_case"
          then begin
            if
              not
                (String.starts_with
                   ~prefix:"match-engine-character-classes-exact:"
                   (field "exactness_case_id" row))
            then Alcotest.failf
                "%s: covered row must have match-engine-character-classes-exact case id"
                (field "requirement_id" row)
          end
          else if
            field "exactness_evidence_kind" row
            = "match_engine_concatenation_exact_case"
          then begin
            if
              not
                (String.starts_with ~prefix:"match-engine-concatenation-exact:"
                   (field "exactness_case_id" row))
            then Alcotest.failf
                "%s: covered row must have match-engine-concatenation-exact case id"
                (field "requirement_id" row)
          end
          else if
            field "exactness_evidence_kind" row
            = "match_engine_backreference_exact_case"
          then begin
            if
              not
                (String.starts_with ~prefix:"match-engine-backreference-exact:"
                   (field "exactness_case_id" row))
            then Alcotest.failf
                "%s: covered row must have match-engine-backreference-exact case id"
                (field "requirement_id" row)
          end
          else if
            field "exactness_evidence_kind" row
            = "match_engine_backreference_matcher_exact_case"
          then begin
            if
              not
                (String.starts_with
                   ~prefix:"match-engine-backreference-matcher-exact:"
                   (field "exactness_case_id" row))
            then Alcotest.failf
                "%s: covered row must have match-engine-backreference-matcher-exact case id"
                (field "requirement_id" row)
          end
          else if
             field "exactness_evidence_kind" row
             = "match_engine_result_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-result-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-result-exact case id"
                 (field "requirement_id" row)
           end
           else if
             field "exactness_evidence_kind" row
             = "match_engine_start_anchor_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-start-anchor-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-start-anchor-exact case id"
                 (field "requirement_id" row)
           end
           else if
             field "exactness_evidence_kind" row
             = "match_engine_end_anchor_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-end-anchor-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-end-anchor-exact case id"
                 (field "requirement_id" row)
           end
           else if
             field "exactness_evidence_kind" row
             = "match_engine_quantifier_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-quantifier-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-quantifier-exact case id"
                 (field "requirement_id" row)
           end
           else if
             field "exactness_evidence_kind" row
             = "match_engine_modifier_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-modifier-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-modifier-exact case id"
                 (field "requirement_id" row)
           end
           else if
             field "exactness_evidence_kind" row
             = "match_engine_assertion_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-assertion-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-assertion-exact case id"
                 (field "requirement_id" row)
           end
           else if
             field "exactness_evidence_kind" row
             = "match_engine_pattern_semantics_exact_case"
           then begin
             if
               not
                 (String.starts_with
                    ~prefix:"match-engine-pattern-semantics-exact:"
                    (field "exactness_case_id" row))
           then Alcotest.failf
                "%s: covered row must have match-engine-pattern-semantics-exact case id"
                (field "requirement_id" row)
           end
           else if
             field "exactness_evidence_kind" row
             = "match_engine_annex_b_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-engine-annex-b-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-engine-annex-b-exact case id"
                 (field "requirement_id" row)
           end
           else if field "exactness_evidence_kind" row = "match_state_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"match-state-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have match-state-exact case id"
                 (field "requirement_id" row)
           end
           else Alcotest.failf
               "%s: unexpected match-engine exactness evidence kind %s"
               (field "requirement_id" row)
               (field "exactness_evidence_kind" row)
         end
         else if field "ledger_state" row = "covered_by_local_exact_compile_parser" then begin
           Alcotest.(check string)
             "local exactness evidence kind"
             "local_exact_compile_parser_case"
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "local exactness credit"
             "local_exact_compile_parser_requirement_credit"
             (field "exactness_coverage_credit" row);
           if
             not
               (String.starts_with ~prefix:"local-exact:"
                  (field "exactness_case_id" row))
           then Alcotest.failf "%s: covered row must have local-exact case id"
               (field "requirement_id" row)
         end
         else if field "ledger_state" row = "covered_by_exec_result_exact" then begin
           Alcotest.(check string)
             "exec-result exactness evidence kind"
             "true"
             (string_of_bool
                (field "exactness_evidence_kind" row
                 = "exec_result_matching_exact_case"
                 || field "exactness_evidence_kind" row
                    = "exec_result_exec_exact_case"
                 || field "exactness_evidence_kind" row
                    = "exec_result_capture_exact_case"
                 || field "exactness_evidence_kind" row
                    = "exec_result_indices_exact_case"
                 || field "exactness_evidence_kind" row
                    = "exec_result_instances_exact_case"));
           Alcotest.(check string)
             "exec-result exactness credit"
             "exec_result_exact_requirement_credit"
             (field "exactness_coverage_credit" row);
           if field "exactness_evidence_kind" row = "exec_result_matching_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"exec-result-matching-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have exec-result-matching-exact case id"
                 (field "requirement_id" row)
           end
           else if field "exactness_evidence_kind" row = "exec_result_exec_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"exec-result-exec-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have exec-result-exec-exact case id"
                 (field "requirement_id" row)
           end
           else if field "exactness_evidence_kind" row = "exec_result_capture_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"exec-result-capture-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have exec-result-capture-exact case id"
                 (field "requirement_id" row)
           end
           else if field "exactness_evidence_kind" row = "exec_result_indices_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"exec-result-indices-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have exec-result-indices-exact case id"
                 (field "requirement_id" row)
           end
           else if field "exactness_evidence_kind" row = "exec_result_instances_exact_case"
           then begin
             if
               not
                 (String.starts_with ~prefix:"exec-result-instances-exact:"
                    (field "exactness_case_id" row))
             then Alcotest.failf
                 "%s: covered row must have exec-result-instances-exact case id"
                 (field "requirement_id" row)
           end
           else Alcotest.failf "%s: unsupported exec-result evidence kind %s"
               (field "requirement_id" row)
               (field "exactness_evidence_kind" row)
         end
         else if field "ledger_state" row = "covered_by_spec_model_exact" then begin
           Alcotest.(check string)
             "spec-model exactness evidence kind"
             "spec_model_exact_case"
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "spec-model exactness credit"
             "spec_model_exact_requirement_credit"
             (field "exactness_coverage_credit" row);
           if
             not
               (String.starts_with ~prefix:"spec-model-exact:"
                  (field "exactness_case_id" row))
         then Alcotest.failf "%s: covered row must have spec-model-exact case id"
             (field "requirement_id" row)
         end
         else if field "ledger_state" row = "covered_by_test262_literal_lexer_exact" then begin
           Alcotest.(check string)
             "test262 literal-lexer exactness evidence kind"
             "test262_literal_lexer_exact_case"
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "test262 literal-lexer exactness credit"
             "test262_literal_lexer_requirement_credit"
             (field "exactness_coverage_credit" row);
           if
             not
               (String.starts_with ~prefix:"test262-regexp-executable:"
                  (field "exactness_case_id" row))
           then Alcotest.failf
               "%s: covered row must have test262-regexp-executable case id"
               (field "requirement_id" row);
           if
             not
               (String.starts_with ~prefix:"test/"
                  (field "exactness_case_source" row))
           then Alcotest.failf "%s: covered row must have test262 case source"
               (field "requirement_id" row)
         end
         else begin
           Alcotest.(check string)
             "reused exactness evidence kind"
             "reused_candidate_exact_compile_parser_case"
             (field "exactness_evidence_kind" row);
           Alcotest.(check string)
             "reused exactness credit"
             "reused_candidate_exact_compile_parser_requirement_credit"
             (field "exactness_coverage_credit" row);
           if
             not
               (String.starts_with ~prefix:"reused-exact:"
                  (field "exactness_case_id" row))
           then Alcotest.failf "%s: covered row must have reused-exact case id"
               (field "requirement_id" row)
         end;
         if
           field "ledger_state" row <> "covered_by_search_adapter"
           && field "ledger_state" row <> "covered_by_match_adapter"
           && field "ledger_state" row <> "covered_by_match_all_adapter"
           && field "ledger_state" row <> "covered_by_split_adapter"
           && field "ledger_state" row <> "covered_by_replace_adapter"
           && field "ledger_state" row <> "covered_by_escape_adapter"
           && field "ledger_state" row <> "covered_by_ucd_generated_tests"
           && not (source_exists (field "exactness_case_source" row))
         then
           Alcotest.failf "%s: covered row source missing: %s"
             (field "requirement_id" row)
             (field "exactness_case_source" row)
       end
       else if field "exactness_coverage_credit" row <> "" then
         Alcotest.failf "%s: non-covered row has exactness credit %s"
           (field "requirement_id" row)
           (field "exactness_coverage_credit" row))
    rows

let () =
  Alcotest.run "ecma262-coverage-ledger" [
    ("manifest", [
      Alcotest.test_case "coverage ledger counts and exactness overlay" `Quick
        test_coverage_ledger_manifest;
    ]);
  ]
