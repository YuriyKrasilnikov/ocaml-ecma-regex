let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-exactness-audit.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-exactness-audit.tsv is missing; run \
           tools/build_ecma262_regexp_exactness_audit.py"
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

let audit_rows () = read_tsv [ "cache"; "ecma262-regexp-exactness-audit.tsv" ]

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

let source_exists case_source =
  if String.starts_with ~prefix:"external/ecma262/" case_source then
    match String.split_on_char '#' case_source with
    | source_path :: _ -> Sys.file_exists (path [ source_path ])
    | [] -> false
  else
    match String.split_on_char ':' case_source with
    | source_path :: _ ->
        Sys.file_exists (path [ "external"; "test262"; source_path ])
    | [] -> false

let test_exactness_manifest () =
  let rows = audit_rows () in
  Alcotest.(check int) "exactness audit rows" 1554 (List.length rows);
  let state_counts = count_by "exactness_audit_state" rows in
  check_count state_counts "covered_by_compile_parser_exact" 21;
  check_count state_counts "covered_by_literal_lexer_exact" 3;
  check_count state_counts "covered_by_local_exact_compile_parser" 319;
  check_count state_counts "covered_by_match_engine_exact" 404;
  check_count state_counts "covered_by_exec_result_exact" 144;
  check_count state_counts "covered_by_spec_model_exact" 4;
  check_count state_counts "covered_by_test262_literal_lexer_exact" 25;
  check_count state_counts "covered_by_reused_candidate_exact_compile_parser"
    224;
  check_count state_counts "open_missing_selector_coverage" 0;
  check_count state_counts "open_local_exact_executable_credit_pending" 0;
  check_count state_counts "open_no_case_negative_or_local_exact" 0;
  check_count state_counts "open_reused_candidate_needs_exact_proof" 0;
  check_count state_counts "open_reused_candidate_manual_spec_review_required" 0;
  check_count state_counts "open_unmapped_negative_syntax_case" 410;
  check_count state_counts "potential_exact_ready_manual_review" 0;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "compile_parser_exact_requirement_credit" 21;
  check_count credit_counts "literal_lexer_exact_requirement_credit" 3;
  check_count credit_counts "local_exact_compile_parser_requirement_credit" 319;
  check_count credit_counts "match_engine_exact_requirement_credit" 404;
  check_count credit_counts "exec_result_exact_requirement_credit" 144;
  check_count credit_counts "spec_model_exact_requirement_credit" 4;
  check_count credit_counts "test262_literal_lexer_requirement_credit" 25;
  check_count credit_counts
    "reused_candidate_exact_compile_parser_requirement_credit" 224;
  check_count credit_counts "none_missing_selector_coverage" 0;
  check_count credit_counts "none_local_exact_executable_pending_credit" 0;
  check_count credit_counts "none_no_executable_case" 0;
  check_count credit_counts "none_reused_candidate" 0;
  check_count credit_counts "none_unmapped_corpus" 410;
  check_count credit_counts "none_manual_review_required" 0;
  let kind_counts = count_by "evidence_kind" rows in
  check_count kind_counts "compile_parser_exact_case" 21;
  check_count kind_counts "literal_lexer_exact_case" 3;
  check_count kind_counts "local_exact_compile_parser_case" 319;
  check_count kind_counts "match_engine_atoms_exact_case" 19;
  check_count kind_counts "match_engine_backreference_exact_case" 11;
  check_count kind_counts "match_engine_backreference_matcher_exact_case" 24;
  check_count kind_counts "match_engine_capture_exact_case" 23;
  check_count kind_counts "match_engine_unicode_sets_string_exact_case" 17;
  check_count kind_counts "match_engine_unicode_sets_escape_string_exact_case"
    16;
  check_count kind_counts "match_engine_character_classes_exact_case" 11;
  check_count kind_counts "match_engine_concatenation_exact_case" 14;
  check_count kind_counts "match_engine_exact_case" 10;
  check_count kind_counts "match_engine_result_exact_case" 1;
  check_count kind_counts "exec_result_matching_exact_case" 72;
  check_count kind_counts "exec_result_exec_exact_case" 21;
  check_count kind_counts "exec_result_capture_exact_case" 13;
  check_count kind_counts "exec_result_indices_exact_case" 35;
  check_count kind_counts "exec_result_instances_exact_case" 3;
  check_count kind_counts "spec_model_exact_case" 4;
  check_count kind_counts "test262_literal_lexer_exact_case" 25;
  check_count kind_counts "match_engine_start_anchor_exact_case" 3;
  check_count kind_counts "match_engine_end_anchor_exact_case" 3;
  check_count kind_counts "match_engine_assertion_exact_case" 89;
  check_count kind_counts "match_engine_quantifier_exact_case" 45;
  check_count kind_counts "match_engine_modifier_exact_case" 10;
  check_count kind_counts "match_engine_pattern_semantics_exact_case" 56;
  check_count kind_counts "match_engine_annex_b_exact_case" 49;
  check_count kind_counts "match_state_exact_case" 3;
  check_count kind_counts "reused_candidate_exact_compile_parser_case" 224;
  check_count kind_counts "selected_compile_positive_case" 0;
  check_count kind_counts "open_reused_candidate_manual_spec_review" 0;
  check_count kind_counts "open_negative_or_local_exact_mapping" 0;
  check_count kind_counts "unmapped_negative_syntax_case" 410;
  let action_counts = count_by "next_action" rows in
  check_count action_counts "add_selector_complete_case_or_local_exact_test" 0;
  check_count action_counts
    "connect_local_exact_executable_evidence_to_requirement_credit" 0;
  check_count action_counts "none_covered_by_compile_parser_exact" 21;
  check_count action_counts "none_covered_by_literal_lexer_exact" 3;
  check_count action_counts "none_covered_by_local_exact_compile_parser" 319;
  check_count action_counts "none_covered_by_match_engine_exact" 404;
  check_count action_counts "none_covered_by_exec_result_exact" 144;
  check_count action_counts "none_covered_by_spec_model_exact" 4;
  check_count action_counts "none_covered_by_test262_literal_lexer_exact" 25;
  check_count action_counts
    "none_covered_by_reused_candidate_exact_compile_parser" 224;
  check_count action_counts "split_reused_candidate_or_add_local_exact_test" 0;
  check_count action_counts "manual_spec_exactness_review_before_credit" 0;
  check_count action_counts "select_negative_syntax_or_local_exact_case" 0;
  check_count action_counts "map_negative_syntax_case_to_requirement" 410;
  List.iter
    (fun row ->
      if
        field "evidence_kind" row <> "compile_parser_exact_case"
        && field "evidence_kind" row <> "literal_lexer_exact_case"
        && field "evidence_kind" row <> "local_exact_compile_parser_case"
        && field "evidence_kind" row <> "match_engine_atoms_exact_case"
        && field "evidence_kind" row <> "match_engine_backreference_exact_case"
        && field "evidence_kind" row
           <> "match_engine_backreference_matcher_exact_case"
        && field "evidence_kind" row <> "match_engine_capture_exact_case"
        && field "evidence_kind" row
           <> "match_engine_unicode_sets_string_exact_case"
        && field "evidence_kind" row
           <> "match_engine_unicode_sets_escape_string_exact_case"
        && field "evidence_kind" row
           <> "match_engine_character_classes_exact_case"
        && field "evidence_kind" row <> "match_engine_concatenation_exact_case"
        && field "evidence_kind" row <> "match_engine_exact_case"
        && field "evidence_kind" row <> "match_engine_result_exact_case"
        && field "evidence_kind" row <> "exec_result_matching_exact_case"
        && field "evidence_kind" row <> "exec_result_exec_exact_case"
        && field "evidence_kind" row <> "exec_result_capture_exact_case"
        && field "evidence_kind" row <> "exec_result_indices_exact_case"
        && field "evidence_kind" row <> "exec_result_instances_exact_case"
        && field "evidence_kind" row <> "spec_model_exact_case"
        && field "evidence_kind" row <> "test262_literal_lexer_exact_case"
        && field "evidence_kind" row <> "match_engine_start_anchor_exact_case"
        && field "evidence_kind" row <> "match_engine_end_anchor_exact_case"
        && field "evidence_kind" row <> "match_engine_assertion_exact_case"
        && field "evidence_kind" row <> "match_engine_quantifier_exact_case"
        && field "evidence_kind" row <> "match_engine_modifier_exact_case"
        && field "evidence_kind" row
           <> "match_engine_pattern_semantics_exact_case"
        && field "evidence_kind" row <> "match_engine_annex_b_exact_case"
        && field "evidence_kind" row <> "match_state_exact_case"
        && field "evidence_kind" row
           <> "reused_candidate_exact_compile_parser_case"
        && not (String.starts_with ~prefix:"none" (field "coverage_credit" row))
      then
        Alcotest.failf "%s: unexpected non-local-exact coverage credit"
          (field "audit_id" row);
      if
        field "case_source" row <> ""
        && not (source_exists (field "case_source" row))
      then
        Alcotest.failf "%s: missing test262 source %s" (field "audit_id" row)
          (field "case_source" row);
      if
        field "exactness_audit_state" row
        = "potential_exact_ready_manual_review"
      then
        Alcotest.failf "%s: exact-ready rows are intentionally zero in v1"
          (field "audit_id" row);
      if field "evidence_kind" row = "compile_parser_exact_case" then begin
        Alcotest.(check string)
          "compile/parser exact state" "covered_by_compile_parser_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "compile/parser exact credit"
          "compile_parser_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "compile/parser exact next action"
          "none_covered_by_compile_parser_exact" (field "next_action" row);
        Alcotest.(check string)
          "compile/parser exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "compile/parser exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        if
          not
            (String.starts_with ~prefix:"compile-parser-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: compile/parser exact case_id must use compile-parser-exact \
             prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: compile/parser exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "literal_lexer_exact_case" then begin
        Alcotest.(check string)
          "literal lexer exact state" "covered_by_literal_lexer_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "literal lexer exact credit" "literal_lexer_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "literal lexer exact next action"
          "none_covered_by_literal_lexer_exact" (field "next_action" row);
        Alcotest.(check string)
          "literal lexer exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "literal lexer exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        if
          not
            (String.starts_with ~prefix:"literal-lexer-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: literal lexer exact case_id must use literal-lexer-exact \
             prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: literal lexer exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_atoms_exact_case" then begin
        Alcotest.(check string)
          "match-engine atom exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine atom exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine atom exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine atom exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine atom exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        if field "expected_behavior" row = "" then
          Alcotest.failf "%s: match-engine atom expected behavior is empty"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-atoms-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine atom exact case_id must use \
             match-engine-atoms-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine atom exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_capture_exact_case" then begin
        Alcotest.(check string)
          "match-engine capture exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine capture exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine capture exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine capture exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine capture exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine capture exact expected behavior"
          "capture_model_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-capture-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine capture exact case_id must use \
             match-engine-capture-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine capture exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if
        field "evidence_kind" row
        = "match_engine_unicode_sets_string_exact_case"
      then begin
        Alcotest.(check string)
          "match-engine UnicodeSets string exact state"
          "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine UnicodeSets string exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine UnicodeSets string exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine UnicodeSets string exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine UnicodeSets string exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine UnicodeSets string exact expected behavior"
          "unicode_sets_string_element_model_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with
               ~prefix:"match-engine-unicode-sets-string-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine UnicodeSets string exact case_id must use \
             match-engine-unicode-sets-string-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine UnicodeSets string exact case_source must use \
             ECMA source"
            (field "audit_id" row)
      end;
      if
        field "evidence_kind" row
        = "match_engine_unicode_sets_escape_string_exact_case"
      then begin
        Alcotest.(check string)
          "match-engine UnicodeSets escape string exact state"
          "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine UnicodeSets escape string exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine UnicodeSets escape string exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine UnicodeSets escape string exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine UnicodeSets escape string exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine UnicodeSets escape string exact expected behavior"
          "unicode_sets_string_element_model_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with
               ~prefix:"match-engine-unicode-sets-escape-string-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine UnicodeSets escape string exact case_id must use \
             match-engine-unicode-sets-escape-string-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine UnicodeSets escape string exact case_source must \
             use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_character_classes_exact_case"
      then begin
        Alcotest.(check string)
          "match-engine character-class exact state"
          "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine character-class exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine character-class exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine character-class exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine character-class exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine character-class exact expected behavior present" "true"
          (string_of_bool
             (field "expected_behavior" row
              = "character_range_exact_plan_observable"
             || field "expected_behavior" row
                = "character_complement_exact_plan_observable"));
        if
          not
            (String.starts_with ~prefix:"match-engine-character-classes-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine character-class exact case_id must use \
             match-engine-character-classes-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine character-class exact case_source must use ECMA \
             source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_concatenation_exact_case"
      then begin
        Alcotest.(check string)
          "match-engine MatchSequence exact state"
          "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine MatchSequence exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine MatchSequence exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine MatchSequence exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine MatchSequence exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine MatchSequence exact expected behavior"
          "match_sequence_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-concatenation-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine MatchSequence exact case_id must use \
             match-engine-concatenation-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine MatchSequence exact case_source must use ECMA \
             source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_backreference_exact_case"
      then begin
        Alcotest.(check string)
          "match-engine backreference exact state"
          "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine backreference exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine backreference exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine backreference exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine backreference exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine backreference exact expected behavior"
          "backreference_model_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-backreference-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine backreference exact case_id must use \
             match-engine-backreference-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine backreference exact case_source must use ECMA \
             source"
            (field "audit_id" row)
      end;
      if
        field "evidence_kind" row
        = "match_engine_backreference_matcher_exact_case"
      then begin
        Alcotest.(check string)
          "match-engine BackreferenceMatcher exact state"
          "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine BackreferenceMatcher exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine BackreferenceMatcher exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine BackreferenceMatcher exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine BackreferenceMatcher exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine BackreferenceMatcher exact expected behavior"
          "backreference_matcher_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with
               ~prefix:"match-engine-backreference-matcher-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine BackreferenceMatcher exact case_id must use \
             match-engine-backreference-matcher-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine BackreferenceMatcher exact case_source must use \
             ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_exact_case" then begin
        Alcotest.(check string)
          "match-engine exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine exact credit" "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine exact next action" "none_covered_by_match_engine_exact"
          (field "next_action" row);
        Alcotest.(check string)
          "match-engine exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        if
          field "expected_behavior" row <> "search_true"
          && field "expected_behavior" row <> "search_false"
        then
          Alcotest.failf
            "%s: match-engine exact expected behavior must be search_true or \
             search_false"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine exact case_id must use match-engine-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_result_exact_case" then begin
        Alcotest.(check string)
          "match-engine result exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine result exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine result exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine result exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine result exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine result exact expected behavior"
          "exec_left_priority_match"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-result-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine result exact case_id must use \
             match-engine-result-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine result exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "exec_result_matching_exact_case" then begin
        Alcotest.(check string)
          "exec-result matching exact state" "covered_by_exec_result_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "exec-result matching exact credit"
          "exec_result_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "exec-result matching exact next action"
          "none_covered_by_exec_result_exact" (field "next_action" row);
        Alcotest.(check string)
          "exec-result matching exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "exec-result matching exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "exec-result matching exact expected behavior present" "true"
          (string_of_bool
             (String.ends_with ~suffix:"_observed"
                (field "expected_behavior" row)));
        if
          not
            (String.starts_with ~prefix:"exec-result-matching-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: exec-result matching exact case_id must use \
             exec-result-matching-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: exec-result matching exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "exec_result_exec_exact_case" then begin
        Alcotest.(check string)
          "exec-result exec exact state" "covered_by_exec_result_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "exec-result exec exact credit" "exec_result_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "exec-result exec exact next action"
          "none_covered_by_exec_result_exact" (field "next_action" row);
        Alcotest.(check string)
          "exec-result exec exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "exec-result exec exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "exec-result exec exact expected behavior present" "true"
          (string_of_bool
             (List.mem
                (field "expected_behavior" row)
                [
                  "regexp_prototype_exec_result_shape_observable";
                  "regexp_prototype_exec_operation_observable";
                  "regexp_prototype_exec_this_value_observable";
                  "regexp_prototype_exec_requires_matcher_slot";
                  "regexp_prototype_exec_string_argument_observable";
                  "regexp_prototype_exec_delegates_to_builtin_exec";
                  "regexp_prototype_test_operation_observable";
                  "regexp_prototype_test_this_value_observable";
                  "regexp_prototype_test_receiver_type_enforced";
                  "regexp_prototype_test_string_argument_observable";
                  "regexp_prototype_test_calls_regexp_exec";
                  "regexp_prototype_test_returns_false_for_null";
                  "regexp_prototype_test_returns_true_for_match";
                  "match_record_encapsulates_start_end_indices";
                  "match_record_fields_list_observable";
                  "match_record_field_table_observable";
                  "match_record_start_index_non_negative";
                  "match_record_end_index_after_start";
                  "get_match_string_operation_observable";
                  "get_match_string_range_assertion";
                  "get_match_string_returns_substring";
                ]));
        if
          not
            (String.starts_with ~prefix:"exec-result-exec-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: exec-result exec exact case_id must use \
             exec-result-exec-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: exec-result exec exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "exec_result_capture_exact_case" then begin
        Alcotest.(check string)
          "exec-result capture exact state" "covered_by_exec_result_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "exec-result capture exact credit"
          "exec_result_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "exec-result capture exact next action"
          "none_covered_by_exec_result_exact" (field "next_action" row);
        Alcotest.(check string)
          "exec-result capture exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "exec-result capture exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "exec-result capture exact expected behavior present" "true"
          (string_of_bool
             (List.mem
                (field "expected_behavior" row)
                [
                  "exec_result_capture_count_observable";
                  "exec_result_capture_count_matches_regexp_record";
                  "exec_result_capture_count_within_array_limit";
                  "exec_result_reads_capture_slot";
                  "exec_result_detects_undefined_capture";
                  "exec_result_returns_undefined_capture_value";
                  "exec_result_takes_defined_capture_branch";
                  "exec_result_exposes_capture_start";
                  "exec_result_exposes_capture_end";
                  "exec_result_builds_capture_match_record";
                  "exec_result_extracts_captured_value";
                  "exec_result_appends_capture_index_record";
                  "exec_result_writes_capture_result_property";
                ]));
        if
          not
            (String.starts_with ~prefix:"exec-result-capture-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: exec-result capture exact case_id must use \
             exec-result-capture-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: exec-result capture exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "exec_result_indices_exact_case" then begin
        Alcotest.(check string)
          "exec-result indices exact state" "covered_by_exec_result_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "exec-result indices exact credit"
          "exec_result_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "exec-result indices exact next action"
          "none_covered_by_exec_result_exact" (field "next_action" row);
        Alcotest.(check string)
          "exec-result indices exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "exec-result indices exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "exec-result indices exact expected behavior present" "true"
          (string_of_bool
             (List.mem
                (field "expected_behavior" row)
                [
                  "exec_result_indices_list_initialized";
                  "exec_result_group_names_list_initialized";
                  "exec_result_appends_full_match_to_indices";
                  "exec_result_appends_undefined_capture_to_indices";
                  "exec_result_takes_has_indices_branch";
                  "exec_result_builds_indices_array";
                  "exec_result_writes_indices_property";
                  "get_match_index_pair_operation_observable";
                  "get_match_index_pair_range_assertion";
                  "get_match_index_pair_returns_start_end_pair";
                  "make_match_indices_array_operation_observable";
                  "make_match_indices_reads_indices_length";
                  "make_match_indices_length_within_array_limit";
                  "make_match_indices_group_names_length_matches";
                  "make_match_indices_group_names_aligned";
                  "make_match_indices_creates_array";
                  "make_match_indices_takes_has_groups_branch";
                  "make_match_indices_creates_groups_object";
                  "make_match_indices_takes_no_groups_branch";
                  "make_match_indices_groups_undefined_without_groups";
                  "make_match_indices_writes_groups_property";
                  "make_match_indices_iterates_entries";
                  "make_match_indices_reads_index_entry";
                  "make_match_indices_takes_defined_entry_branch";
                  "make_match_indices_calls_get_match_index_pair";
                  "make_match_indices_takes_undefined_entry_branch";
                  "make_match_indices_returns_undefined_pair";
                  "make_match_indices_writes_numeric_property";
                  "make_match_indices_takes_capture_entry_branch";
                  "make_match_indices_reads_group_name";
                  "make_match_indices_takes_named_group_branch";
                  "make_match_indices_asserts_groups_object_for_name";
                  "make_match_indices_allows_duplicate_group_property_write";
                  "make_match_indices_writes_named_group_property";
                  "make_match_indices_returns_array";
                ]));
        if
          not
            (String.starts_with ~prefix:"exec-result-indices-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: exec-result indices exact case_id must use \
             exec-result-indices-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: exec-result indices exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "exec_result_instances_exact_case" then begin
        Alcotest.(check string)
          "exec-result instances exact state" "covered_by_exec_result_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "exec-result instances exact credit"
          "exec_result_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "exec-result instances exact next action"
          "none_covered_by_exec_result_exact" (field "next_action" row);
        Alcotest.(check string)
          "exec-result instances exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "exec-result instances exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "exec-result instances exact expected behavior present" "true"
          (string_of_bool
             (List.mem
                (field "expected_behavior" row)
                [
                  "regexp_instance_internal_slots_observed";
                  "regexp_instance_last_index_property_observed";
                  "last_index_integral_start_property_attributes_observed";
                ]));
        if
          not
            (String.starts_with ~prefix:"exec-result-instances-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: exec-result instances exact case_id must use \
             exec-result-instances-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: exec-result instances exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "spec_model_exact_case" then begin
        Alcotest.(check string)
          "spec-model exact state" "covered_by_spec_model_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "spec-model exact credit" "spec_model_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "spec-model exact next action" "none_covered_by_spec_model_exact"
          (field "next_action" row);
        Alcotest.(check string)
          "spec-model exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "spec-model exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "spec-model exact expected behavior present" "true"
          (string_of_bool
             (List.mem
                (field "expected_behavior" row)
                [
                  "lexical_grammar_source_character_goal_model_observed";
                  "syntactic_token_stream_boundary_policy_observed";
                  "regexp_grammar_pattern_source_model_observed";
                  "lexical_regexp_grammar_notation_boundary_observed";
                ]));
        if
          not
            (String.starts_with ~prefix:"spec-model-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: spec-model exact case_id must use spec-model-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf "%s: spec-model exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "test262_literal_lexer_exact_case" then begin
        Alcotest.(check string)
          "test262 literal-lexer exact state"
          "covered_by_test262_literal_lexer_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "test262 literal-lexer exact credit"
          "test262_literal_lexer_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "test262 literal-lexer exact next action"
          "none_covered_by_test262_literal_lexer_exact"
          (field "next_action" row);
        Alcotest.(check string)
          "test262 literal-lexer exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "test262 literal-lexer exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        if field "expected_behavior" row = "" then
          Alcotest.failf "%s: test262 literal-lexer expected behavior is empty"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"test262-regexp-executable:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: test262 literal-lexer exact case_id must use \
             test262-regexp-executable prefix"
            (field "audit_id" row);
        if not (String.starts_with ~prefix:"test/" (field "case_source" row))
        then
          Alcotest.failf
            "%s: test262 literal-lexer exact case_source must use test262 \
             source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_start_anchor_exact_case" then begin
        Alcotest.(check string)
          "match-engine start-anchor exact state"
          "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine start-anchor exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine start-anchor exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine start-anchor exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine start-anchor exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine start-anchor exact expected behavior"
          "start_anchor_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-start-anchor-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine start-anchor exact case_id must use \
             match-engine-start-anchor-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine start-anchor exact case_source must use ECMA \
             source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_end_anchor_exact_case" then begin
        Alcotest.(check string)
          "match-engine end-anchor exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine end-anchor exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine end-anchor exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine end-anchor exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine end-anchor exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine end-anchor exact expected behavior"
          "end_anchor_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-end-anchor-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine end-anchor exact case_id must use \
             match-engine-end-anchor-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine end-anchor exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_quantifier_exact_case" then begin
        Alcotest.(check string)
          "match-engine quantifier exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine quantifier exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine quantifier exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine quantifier exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine quantifier exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine quantifier exact expected behavior"
          "quantifier_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-quantifier-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine quantifier exact case_id must use \
             match-engine-quantifier-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine quantifier exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_modifier_exact_case" then begin
        Alcotest.(check string)
          "match-engine modifier exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine modifier exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine modifier exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine modifier exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine modifier exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine modifier exact expected behavior"
          "modifier_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-modifier-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine modifier exact case_id must use \
             match-engine-modifier-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine modifier exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_assertion_exact_case" then begin
        Alcotest.(check string)
          "match-engine assertion exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine assertion exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine assertion exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine assertion exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine assertion exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine assertion exact expected behavior"
          "assertion_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-assertion-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine assertion exact case_id must use \
             match-engine-assertion-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine assertion exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_pattern_semantics_exact_case"
      then begin
        Alcotest.(check string)
          "match-engine Pattern Semantics exact state"
          "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine Pattern Semantics exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine Pattern Semantics exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine Pattern Semantics exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine Pattern Semantics exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine Pattern Semantics exact expected behavior"
          "pattern_semantics_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-pattern-semantics-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine Pattern Semantics exact case_id must use \
             match-engine-pattern-semantics-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine Pattern Semantics exact case_source must use \
             ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_engine_annex_b_exact_case" then begin
        Alcotest.(check string)
          "match-engine Annex B exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-engine Annex B exact credit"
          "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-engine Annex B exact next action"
          "none_covered_by_match_engine_exact" (field "next_action" row);
        Alcotest.(check string)
          "match-engine Annex B exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-engine Annex B exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-engine Annex B exact expected behavior"
          "annex_b_exact_plan_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-engine-annex-b-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-engine Annex B exact case_id must use \
             match-engine-annex-b-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-engine Annex B exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "match_state_exact_case" then begin
        Alcotest.(check string)
          "match-state exact state" "covered_by_match_engine_exact"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "match-state exact credit" "match_engine_exact_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "match-state exact next action" "none_covered_by_match_engine_exact"
          (field "next_action" row);
        Alcotest.(check string)
          "match-state exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "match-state exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        Alcotest.(check string)
          "match-state exact expected behavior" "match_state_model_observable"
          (field "expected_behavior" row);
        if
          not
            (String.starts_with ~prefix:"match-state-exact:"
               (field "case_id" row))
        then
          Alcotest.failf
            "%s: match-state exact case_id must use match-state-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf
            "%s: match-state exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "local_exact_compile_parser_case" then begin
        Alcotest.(check string)
          "local exact state" "covered_by_local_exact_compile_parser"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "local exact credit" "local_exact_compile_parser_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "local exact next action" "none_covered_by_local_exact_compile_parser"
          (field "next_action" row);
        Alcotest.(check string)
          "local exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "local exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        if not (String.starts_with ~prefix:"local-exact:" (field "case_id" row))
        then
          Alcotest.failf "%s: local exact case_id must use local-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf "%s: local exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if
        field "evidence_kind" row = "reused_candidate_exact_compile_parser_case"
      then begin
        Alcotest.(check string)
          "reused exact state"
          "covered_by_reused_candidate_exact_compile_parser"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "reused exact credit"
          "reused_candidate_exact_compile_parser_requirement_credit"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "reused exact next action"
          "none_covered_by_reused_candidate_exact_compile_parser"
          (field "next_action" row);
        Alcotest.(check string)
          "reused exact reuse count" "1"
          (field "case_reuse_count" row);
        Alcotest.(check string)
          "reused exact missing selectors" ""
          (field "selected_missing_selector_tags" row);
        if
          not (String.starts_with ~prefix:"reused-exact:" (field "case_id" row))
        then
          Alcotest.failf "%s: reused exact case_id must use reused-exact prefix"
            (field "audit_id" row);
        if
          not
            (String.starts_with ~prefix:"external/ecma262/"
               (field "case_source" row))
        then
          Alcotest.failf "%s: reused exact case_source must use ECMA source"
            (field "audit_id" row)
      end;
      if field "evidence_kind" row = "open_reused_candidate_manual_spec_review"
      then begin
        Alcotest.(check string)
          "manual reused state"
          "open_reused_candidate_manual_spec_review_required"
          (field "exactness_audit_state" row);
        Alcotest.(check string)
          "manual reused credit" "none_manual_review_required"
          (field "coverage_credit" row);
        Alcotest.(check string)
          "manual reused next action"
          "manual_spec_exactness_review_before_credit" (field "next_action" row);
        Alcotest.(check string) "manual reused case id" "" (field "case_id" row)
      end)
    rows

let () =
  Alcotest.run "ecma262-exactness-audit"
    [
      ( "manifest",
        [
          Alcotest.test_case "exactness audit invariants" `Quick
            test_exactness_manifest;
        ] );
    ]
