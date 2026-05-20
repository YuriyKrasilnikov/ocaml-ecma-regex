type expected =
  | Match of { start_index : int; end_index : int; matched_units : int list }
  | No_match

type exec_case = {
  exec_name : string;
  exec_pattern : string;
  exec_flags : string;
  exec_input_units : int list;
  exec_expected : expected;
}

type search_case = {
  search_name : string;
  search_pattern : string;
  search_flags : string;
  search_input_units : int list;
  search_expected : bool;
}

type instance_case = {
  instance_name : string;
  instance_pattern : string;
  instance_flags : string;
  instance_input_units : int list;
  instance_last_index : int;
  instance_expected : expected;
  instance_expected_last_index : int;
}

let flags_or_fail source =
  match Ecma_regex.flags_of_string source with
  | Ok flags -> flags
  | Error msg -> Alcotest.failf "invalid flags %S: %s" source msg

let compile_or_fail ~flags source =
  match Ecma_regex.compile ~flags source with
  | Ok regexp -> regexp
  | Error msg -> Alcotest.failf "compile %S failed: %s" source msg

let js_string_of_utf16_units_or_fail units =
  match Ecma_regex.js_string_of_utf16_code_units units with
  | Ok input -> input
  | Error msg -> Alcotest.failf "invalid UTF-16 input: %s" msg

let match_ ?(start_index = 0) ?end_index matched_units =
  let end_index =
    match end_index with
    | Some index -> index
    | None -> start_index + List.length matched_units
  in
  Match { start_index; end_index; matched_units }

let exec_case ?(flags = "") name pattern input_units expected =
  {
    exec_name = name;
    exec_pattern = pattern;
    exec_flags = flags;
    exec_input_units = input_units;
    exec_expected = expected;
  }

let search_case ?(flags = "") name pattern input_units expected =
  {
    search_name = name;
    search_pattern = pattern;
    search_flags = flags;
    search_input_units = input_units;
    search_expected = expected;
  }

let instance_case name ~flags ~last_index ~expected_last_index pattern
    input_units expected =
  {
    instance_name = name;
    instance_pattern = pattern;
    instance_flags = flags;
    instance_input_units = input_units;
    instance_last_index = last_index;
    instance_expected = expected;
    instance_expected_last_index = expected_last_index;
  }

let check_match_result name ~start_index ~end_index ~matched_units actual =
  Alcotest.(check int)
    (name ^ ": start_index") start_index actual.Ecma_regex.js_start_index;
  Alcotest.(check int)
    (name ^ ": end_index") end_index actual.Ecma_regex.js_end_index;
  Alcotest.(check (list int))
    (name ^ ": matched UTF-16 units")
    matched_units
    (Ecma_regex.js_string_to_utf16_code_units actual.Ecma_regex.js_matched_text)

let check_expected_result name expected actual =
  match (expected, actual) with
  | No_match, None -> ()
  | No_match, Some actual ->
      Alcotest.failf "%s: unexpected match at UTF-16 %d..%d" name
        actual.Ecma_regex.js_start_index actual.Ecma_regex.js_end_index
  | Match _, None -> Alcotest.failf "%s: expected a match" name
  | Match { start_index; end_index; matched_units }, Some actual ->
      check_match_result name ~start_index ~end_index ~matched_units actual

let run_exec_case
    { exec_name; exec_pattern; exec_flags; exec_input_units; exec_expected } ()
    =
  let flags = flags_or_fail exec_flags in
  let regexp = compile_or_fail ~flags exec_pattern in
  let input = js_string_of_utf16_units_or_fail exec_input_units in
  check_expected_result exec_name exec_expected
    (Ecma_regex.exec_js regexp input)

let run_search_case
    {
      search_name;
      search_pattern;
      search_flags;
      search_input_units;
      search_expected;
    } () =
  let flags = flags_or_fail search_flags in
  let regexp = compile_or_fail ~flags search_pattern in
  let input = js_string_of_utf16_units_or_fail search_input_units in
  Alcotest.(check bool)
    search_name search_expected
    (Ecma_regex.search_js regexp input)

let run_instance_case
    {
      instance_name;
      instance_pattern;
      instance_flags;
      instance_input_units;
      instance_last_index;
      instance_expected;
      instance_expected_last_index;
    } () =
  let flags = flags_or_fail instance_flags in
  let regexp = compile_or_fail ~flags instance_pattern in
  let instance = Ecma_regex.instance regexp in
  let input = js_string_of_utf16_units_or_fail instance_input_units in
  Ecma_regex.set_last_index instance instance_last_index;
  check_expected_result instance_name instance_expected
    (Ecma_regex.exec_instance_js instance input);
  Alcotest.(check int)
    (instance_name ^ ": last_index")
    instance_expected_last_index
    (Ecma_regex.last_index instance)

let high = 0xD83D
let low = 0xDE00
let letter_a = 0x0041
let grinning_face = [ high; low ]
let grinning_then_a = [ high; low; letter_a ]
let high_then_a = [ high; letter_a ]
let a_then_low = [ letter_a; low ]
let grinning_then_low = [ high; low; low ]
let grinning_then_high = [ high; low; high ]

let exec_cases =
  [
    exec_case ~flags:"u"
      "exec /u does not search for low surrogate inside valid pair" "\\uDE00"
      grinning_face No_match;
    exec_case ~flags:"u"
      "exec /u class does not search for low surrogate inside valid pair"
      "[\\uDE00]" grinning_face No_match;
    exec_case ~flags:"u"
      "exec /u lookahead does not probe low surrogate inside valid pair"
      "(?=\\uDE00)" grinning_face No_match;
    exec_case ~flags:"u" "exec /u matches lone low surrogate after BMP prefix"
      "\\uDE00" a_then_low
      (match_ ~start_index:1 [ low ]);
    exec_case ~flags:"u"
      "exec /u skips valid pair and matches trailing lone low surrogate"
      "\\uDE00" grinning_then_low
      (match_ ~start_index:2 [ low ]);
    exec_case ~flags:"u"
      "exec /u skips high surrogate that forms pair before trailing high"
      "\\uD83D" grinning_then_high
      (match_ ~start_index:2 [ high ]);
    exec_case "exec without Unicode can search low surrogate inside pair"
      "\\uDE00" grinning_face
      (match_ ~start_index:1 [ low ]);
    exec_case ~flags:"u"
      "exec /u dot consumes broken high surrogate as one code unit" "."
      high_then_a (match_ [ high ]);
    exec_case ~flags:"u"
      "exec /u property complement skips emoji pair before matching A"
      "\\P{Emoji}" grinning_then_a
      (match_ ~start_index:2 [ letter_a ]);
    exec_case ~flags:"u"
      "exec /u class property complement skips emoji pair before matching A"
      "[\\P{Emoji}]" grinning_then_a
      (match_ ~start_index:2 [ letter_a ]);
    exec_case ~flags:"u"
      "exec /u inverted property class skips emoji pair before matching A"
      "[^\\p{Emoji}]" grinning_then_a
      (match_ ~start_index:2 [ letter_a ]);
    exec_case ~flags:"u"
      "exec /u boundary plus low surrogate does not match inside valid pair"
      "\\B\\uDE00" grinning_face No_match;
    exec_case ~flags:"u"
      "exec /u boundary plus property complement does not match inside emoji \
       pair"
      "\\B\\P{Emoji}" grinning_then_a No_match;
    exec_case ~flags:"u" "exec /u word boundary skips pair and appears before A"
      "\\b" grinning_then_a
      (match_ ~start_index:2 ~end_index:2 []);
  ]

let search_cases =
  [
    search_case ~flags:"u"
      "search_js /u does not report low surrogate inside valid pair" "\\uDE00"
      grinning_face false;
    search_case
      "search_js without Unicode reports low surrogate inside valid pair"
      "\\uDE00" grinning_face true;
    search_case ~flags:"u"
      "search_js /u reports trailing low surrogate after valid pair" "\\uDE00"
      grinning_then_low true;
    search_case ~flags:"u"
      "search_js /u boundary-property complement avoids inside-pair false \
       positive"
      "\\B\\P{Emoji}" grinning_then_a false;
  ]

let instance_cases =
  [
    instance_case "global /gu low surrogate search skips valid pair and resets"
      ~flags:"gu" ~last_index:0 ~expected_last_index:0 "\\uDE00" grinning_face
      No_match;
    instance_case "global /g low surrogate search can match inside pair"
      ~flags:"g" ~last_index:0 ~expected_last_index:2 "\\uDE00" grinning_face
      (match_ ~start_index:1 [ low ]);
    instance_case "sticky /uy low surrogate at pair start rejects and resets"
      ~flags:"uy" ~last_index:0 ~expected_last_index:0 "\\uDE00" grinning_face
      No_match;
    instance_case "sticky /uy low surrogate at explicit low index matches"
      ~flags:"uy" ~last_index:1 ~expected_last_index:2 "\\uDE00" grinning_face
      (match_ ~start_index:1 [ low ]);
    instance_case "sticky /uy dot at pair start consumes full pair" ~flags:"uy"
      ~last_index:0 ~expected_last_index:2 "." grinning_face
      (match_ grinning_face);
    instance_case "sticky /uy dot at explicit low index consumes low surrogate"
      ~flags:"uy" ~last_index:1 ~expected_last_index:2 "." grinning_face
      (match_ ~start_index:1 [ low ]);
    instance_case
      "sticky /uy boundary plus low surrogate at explicit low index matches"
      ~flags:"uy" ~last_index:1 ~expected_last_index:2 "\\B\\uDE00"
      grinning_face
      (match_ ~start_index:1 [ low ]);
    instance_case "global /gu property complement skips emoji pair before A"
      ~flags:"gu" ~last_index:0 ~expected_last_index:3 "\\P{Emoji}"
      grinning_then_a
      (match_ ~start_index:2 [ letter_a ]);
  ]

let test_unicode_empty_iterator_advances_over_pair () =
  let flags = flags_or_fail "gu" in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  let input = js_string_of_utf16_units_or_fail grinning_face in
  let iterator = Ecma_regex.iter_matches_js instance input in
  check_expected_result "iterator /gu empty at pair start"
    (match_ ~end_index:0 [])
    (Ecma_regex.next_match_js iterator);
  Alcotest.(check int)
    "iterator /gu last_index after pair-start empty" 2
    (Ecma_regex.last_index instance)

let test_non_unicode_empty_iterator_advances_one_code_unit () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  let input = js_string_of_utf16_units_or_fail grinning_face in
  let iterator = Ecma_regex.iter_matches_js instance input in
  check_expected_result "iterator /g empty at pair start"
    (match_ ~end_index:0 [])
    (Ecma_regex.next_match_js iterator);
  Alcotest.(check int)
    "iterator /g last_index after pair-start empty" 1
    (Ecma_regex.last_index instance)

let test_unicode_empty_iterator_from_low_index_advances_one_code_unit () =
  let flags = flags_or_fail "gu" in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  let input = js_string_of_utf16_units_or_fail grinning_face in
  Ecma_regex.set_last_index instance 1;
  let iterator = Ecma_regex.iter_matches_js instance input in
  check_expected_result "iterator /gu empty at explicit low index"
    (match_ ~start_index:1 ~end_index:1 [])
    (Ecma_regex.next_match_js iterator);
  Alcotest.(check int)
    "iterator /gu last_index after explicit low-index empty" 2
    (Ecma_regex.last_index instance)

let test_unicode_iterator_does_not_find_low_inside_pair () =
  let flags = flags_or_fail "gu" in
  let regexp = compile_or_fail ~flags "\\uDE00" in
  let instance = Ecma_regex.instance regexp in
  let input = js_string_of_utf16_units_or_fail grinning_face in
  let iterator = Ecma_regex.iter_matches_js instance input in
  check_expected_result "iterator /gu low surrogate inside pair" No_match
    (Ecma_regex.next_match_js iterator);
  Alcotest.(check int)
    "iterator /gu low surrogate miss resets last_index" 0
    (Ecma_regex.last_index instance)

let exec_tests =
  List.map
    (fun test_case ->
      Alcotest.test_case test_case.exec_name `Quick (run_exec_case test_case))
    exec_cases

let search_tests =
  List.map
    (fun test_case ->
      Alcotest.test_case test_case.search_name `Quick
        (run_search_case test_case))
    search_cases

let instance_tests =
  List.map
    (fun test_case ->
      Alcotest.test_case test_case.instance_name `Quick
        (run_instance_case test_case))
    instance_cases

let iterator_tests =
  [
    Alcotest.test_case "iterator /gu empty advances over valid surrogate pair"
      `Quick test_unicode_empty_iterator_advances_over_pair;
    Alcotest.test_case "iterator /g empty advances one raw code unit" `Quick
      test_non_unicode_empty_iterator_advances_one_code_unit;
    Alcotest.test_case
      "iterator /gu empty from explicit low index advances one code unit" `Quick
      test_unicode_empty_iterator_from_low_index_advances_one_code_unit;
    Alcotest.test_case "iterator /gu does not find low surrogate inside pair"
      `Quick test_unicode_iterator_does_not_find_low_inside_pair;
  ]

let () =
  Alcotest.run "raw-utf16-negative-position-matrix"
    [
      ("exec_js negative positions", exec_tests);
      ("search_js negative positions", search_tests);
      ("exec_instance_js positions", instance_tests);
      ("iter_matches_js positions", iterator_tests);
    ]
