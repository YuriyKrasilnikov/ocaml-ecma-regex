type expected_slice = {
  prefix_units : int list;
  matched_units : int list;
  suffix_units : int list;
}

type exec_case = {
  exec_name : string;
  exec_pattern : string;
  exec_flags : string;
  exec_expected : expected_slice;
}

type instance_case = {
  instance_name : string;
  instance_pattern : string;
  instance_flags : string;
  instance_last_index : int;
  instance_expected_last_index : int;
  instance_expected : expected_slice;
}

type iterator_step = {
  step_expected : expected_slice;
  step_expected_last_index : int;
}

type iterator_case = {
  iterator_name : string;
  iterator_pattern : string;
  iterator_flags : string;
  iterator_initial_last_index : int;
  iterator_input_units : int list;
  iterator_steps : iterator_step list;
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

let expected prefix_units matched_units suffix_units =
  { prefix_units; matched_units; suffix_units }

let input_units_of_expected expected =
  expected.prefix_units @ expected.matched_units @ expected.suffix_units

let expected_start_index expected = List.length expected.prefix_units

let expected_end_index expected =
  expected_start_index expected + List.length expected.matched_units

let rec take n units =
  if n <= 0 then []
  else match units with [] -> [] | unit :: rest -> unit :: take (n - 1) rest

let rec drop n units =
  if n <= 0 then units
  else match units with [] -> [] | _ :: rest -> drop (n - 1) rest

let slice start_index end_index units =
  take (end_index - start_index) (drop start_index units)

let check_slice_result name input_units expected actual =
  let expected_start = expected_start_index expected in
  let expected_end = expected_end_index expected in
  Alcotest.(check int)
    (name ^ ": start_index") expected_start actual.Ecma_regex.js_start_index;
  Alcotest.(check int)
    (name ^ ": end_index") expected_end actual.Ecma_regex.js_end_index;
  let actual_matched_units =
    Ecma_regex.js_string_to_utf16_code_units actual.Ecma_regex.js_matched_text
  in
  Alcotest.(check (list int))
    (name ^ ": js_matched_text")
    expected.matched_units actual_matched_units;
  let actual_prefix = take actual.Ecma_regex.js_start_index input_units in
  let actual_match_from_input =
    slice actual.Ecma_regex.js_start_index actual.Ecma_regex.js_end_index
      input_units
  in
  let actual_suffix = drop actual.Ecma_regex.js_end_index input_units in
  Alcotest.(check (list int))
    (name ^ ": prefix slice") expected.prefix_units actual_prefix;
  Alcotest.(check (list int))
    (name ^ ": matched input slice")
    actual_match_from_input actual_matched_units;
  Alcotest.(check (list int))
    (name ^ ": suffix slice") expected.suffix_units actual_suffix;
  Alcotest.(check (list int))
    (name ^ ": reconstructed input")
    input_units
    (actual_prefix @ actual_matched_units @ actual_suffix)

let run_exec_case { exec_name; exec_pattern; exec_flags; exec_expected } () =
  let flags = flags_or_fail exec_flags in
  let regexp = compile_or_fail ~flags exec_pattern in
  let input_units = input_units_of_expected exec_expected in
  let input = js_string_of_utf16_units_or_fail input_units in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.failf "%s: expected a match" exec_name
  | Some actual -> check_slice_result exec_name input_units exec_expected actual

let run_instance_case
    {
      instance_name;
      instance_pattern;
      instance_flags;
      instance_last_index;
      instance_expected_last_index;
      instance_expected;
    } () =
  let flags = flags_or_fail instance_flags in
  let regexp = compile_or_fail ~flags instance_pattern in
  let instance = Ecma_regex.instance regexp in
  let input_units = input_units_of_expected instance_expected in
  let input = js_string_of_utf16_units_or_fail input_units in
  Ecma_regex.set_last_index instance instance_last_index;
  (match Ecma_regex.exec_instance_js instance input with
  | None -> Alcotest.failf "%s: expected a match" instance_name
  | Some actual ->
      check_slice_result instance_name input_units instance_expected actual);
  Alcotest.(check int)
    (instance_name ^ ": last_index")
    instance_expected_last_index
    (Ecma_regex.last_index instance)

let run_iterator_case
    {
      iterator_name;
      iterator_pattern;
      iterator_flags;
      iterator_initial_last_index;
      iterator_input_units;
      iterator_steps;
    } () =
  let flags = flags_or_fail iterator_flags in
  let regexp = compile_or_fail ~flags iterator_pattern in
  let instance = Ecma_regex.instance regexp in
  let input = js_string_of_utf16_units_or_fail iterator_input_units in
  Ecma_regex.set_last_index instance iterator_initial_last_index;
  let iterator = Ecma_regex.iter_matches_js instance input in
  List.iteri
    (fun index { step_expected; step_expected_last_index } ->
      let step_name = Printf.sprintf "%s step %d" iterator_name index in
      match Ecma_regex.next_match_js iterator with
      | None -> Alcotest.failf "%s: expected a match" step_name
      | Some actual ->
          check_slice_result step_name iterator_input_units step_expected actual;
          Alcotest.(check int)
            (step_name ^ ": last_index")
            step_expected_last_index
            (Ecma_regex.last_index instance))
    iterator_steps

let exec_case ?(flags = "") exec_name exec_pattern exec_expected =
  { exec_name; exec_pattern; exec_flags = flags; exec_expected }

let instance_case ?(flags = "") instance_name ~last_index ~expected_last_index
    instance_pattern instance_expected =
  {
    instance_name;
    instance_pattern;
    instance_flags = flags;
    instance_last_index = last_index;
    instance_expected_last_index = expected_last_index;
    instance_expected;
  }

let iterator_case ?(flags = "") iterator_name ?(initial_last_index = 0)
    iterator_pattern iterator_input_units iterator_steps =
  {
    iterator_name;
    iterator_pattern;
    iterator_flags = flags;
    iterator_initial_last_index = initial_last_index;
    iterator_input_units;
    iterator_steps;
  }

let step step_expected step_expected_last_index =
  { step_expected; step_expected_last_index }

let high = 0xD83D
let low = 0xDE00
let letter_a = 0x0041
let letter_b = 0x0042
let long_s = 0x017F
let grinning_face = [ high; low ]
let grinning_then_a = [ high; low; letter_a ]
let grinning_a_grinning = [ high; low; letter_a; high; low ]

let exec_cases =
  [
    exec_case ~flags:"u"
      "exec /u braced literal returns whole surrogate-pair slice" "\\u{1F600}"
      (expected [ letter_a ] grinning_face [ letter_b ]);
    exec_case ~flags:"u"
      "exec /u character class returns whole surrogate-pair slice"
      "[\\u{1F600}]"
      (expected [ letter_a ] grinning_face [ letter_b ]);
    exec_case "exec non-Unicode high surrogate returns high-only slice"
      "\\uD83D"
      (expected [ letter_a ] [ high ] [ low; letter_b ]);
    exec_case "exec non-Unicode low surrogate returns low-only slice" "\\uDE00"
      (expected [ letter_a; high ] [ low ] [ letter_b ]);
    exec_case ~flags:"u"
      "exec /u trailing lone low after pair returns low-only slice" "\\uDE00"
      (expected [ letter_a; high; low ] [ low ] [ letter_b ]);
    exec_case ~flags:"u"
      "exec /u trailing lone high after pair returns high-only slice" "\\uD83D"
      (expected [ letter_a; high; low ] [ high ] [ letter_b ]);
    exec_case ~flags:"u"
      "exec /u property complement skips pair and returns BMP slice"
      "\\P{Emoji}"
      (expected grinning_face [ letter_a ] [ letter_b ]);
    exec_case ~flags:"u"
      "exec /u inverted property class skips pair and returns BMP slice"
      "[^\\p{Emoji}]"
      (expected grinning_face [ letter_a ] [ letter_b ]);
    exec_case ~flags:"u"
      "exec /u word boundary after pair returns empty slice before A" "\\b"
      (expected grinning_face [] [ letter_a ]);
    exec_case ~flags:"u" "exec /u start anchor returns empty prefix slice" "^"
      (expected [] [] grinning_then_a);
    exec_case ~flags:"u" "exec /u end anchor returns empty suffix slice" "$"
      (expected [ letter_a; high; low ] [] []);
    exec_case ~flags:"iu" "exec /iu word character returns folded long-s slice"
      "\\w"
      (expected [ high; low ] [ long_s ] [ letter_b ]);
  ]

let instance_cases =
  [
    instance_case ~flags:"uy"
      "instance /uy dot at pair start returns whole pair slice" ~last_index:1
      ~expected_last_index:3 "."
      (expected [ letter_a ] grinning_face [ letter_b ]);
    instance_case ~flags:"uy"
      "instance /uy dot at explicit low index returns low-only slice"
      ~last_index:2 ~expected_last_index:3 "."
      (expected [ letter_a; high ] [ low ] [ letter_b ]);
    instance_case ~flags:"uy"
      "instance /uy property complement after pair returns BMP slice"
      ~last_index:2 ~expected_last_index:3 "\\P{Emoji}"
      (expected grinning_face [ letter_a ] [ letter_b ]);
    instance_case ~flags:"gy"
      "instance /gy low surrogate at explicit low index returns low-only slice"
      ~last_index:2 ~expected_last_index:3 "\\uDE00"
      (expected [ letter_a; high ] [ low ] [ letter_b ]);
  ]

let iterator_cases =
  [
    iterator_case ~flags:"gu" "iterator /gu empty slicing over pair and BMP" ""
      grinning_then_a
      [
        step (expected [] [] grinning_then_a) 2;
        step (expected grinning_face [] [ letter_a ]) 3;
        step (expected grinning_then_a [] []) 4;
      ];
    iterator_case ~flags:"g" "iterator /g empty slicing one code unit at a time"
      "" grinning_then_a
      [
        step (expected [] [] grinning_then_a) 1;
        step (expected [ high ] [] [ low; letter_a ]) 2;
        step (expected grinning_face [] [ letter_a ]) 3;
      ];
    iterator_case ~flags:"gu"
      "iterator /gu empty slicing from explicit low index" ~initial_last_index:1
      "" grinning_then_a
      [
        step (expected [ high ] [] [ low; letter_a ]) 2;
        step (expected grinning_face [] [ letter_a ]) 3;
      ];
    iterator_case ~flags:"gu"
      "iterator /gu literal pair slices repeated matches" "\\u{1F600}"
      grinning_a_grinning
      [
        step (expected [] grinning_face [ letter_a; high; low ]) 2;
        step (expected [ high; low; letter_a ] grinning_face []) 5;
      ];
  ]

let exec_tests =
  List.map
    (fun test_case ->
      Alcotest.test_case test_case.exec_name `Quick (run_exec_case test_case))
    exec_cases

let instance_tests =
  List.map
    (fun test_case ->
      Alcotest.test_case test_case.instance_name `Quick
        (run_instance_case test_case))
    instance_cases

let iterator_tests =
  List.map
    (fun test_case ->
      Alcotest.test_case test_case.iterator_name `Quick
        (run_iterator_case test_case))
    iterator_cases

let () =
  Alcotest.run "raw-utf16-result-slicing-matrix"
    [
      ("exec_js slicing", exec_tests);
      ("exec_instance_js slicing", instance_tests);
      ("iter_matches_js slicing", iterator_tests);
    ]
