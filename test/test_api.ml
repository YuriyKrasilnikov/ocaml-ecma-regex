let test_compile_accepts_simple_literal () =
  match Ecma_regex.compile "a" with
  | Ok _ -> ()
  | Error msg -> Alcotest.failf "simple literal unexpectedly failed: %s" msg

let test_compile_accepts_anchor_syntax () =
  match Ecma_regex.compile "^abc$" with
  | Ok _ -> ()
  | Error msg -> Alcotest.failf "anchor syntax unexpectedly failed: %s" msg

let test_compile_accepts_character_class_escape () =
  match Ecma_regex.compile "^\\s+$" with
  | Ok _ -> ()
  | Error msg ->
    Alcotest.failf "character class escape unexpectedly failed: %s" msg

let test_compile_accepts_non_unicode_identity_escape () =
  match Ecma_regex.compile "\\-" with
  | Ok _ -> ()
  | Error msg ->
    Alcotest.failf "non-unicode identity escape unexpectedly failed: %s" msg

let test_compile_rejects_unicode_identity_escape () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "\\-" with
    | Error _ -> ()
    | Ok _ -> Alcotest.fail "unicode identity escape unexpectedly succeeded"

let test_compile_accepts_control_escapes () =
  List.iter
    (fun pattern ->
       match Ecma_regex.compile pattern with
       | Ok _ -> ()
       | Error msg ->
         Alcotest.failf "control escape %S unexpectedly failed: %s" pattern msg)
    [ "\\n"; "\\r"; "\\t"; "\\f"; "\\v" ]

let test_compile_accepts_control_letter_escape () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "\\cA" with
    | Ok _ -> ()
    | Error msg -> Alcotest.failf "control-letter escape unexpectedly failed: %s" msg

let test_compile_accepts_dot_atom () =
  match Ecma_regex.compile "." with
  | Ok _ -> ()
  | Error msg -> Alcotest.failf "dot atom unexpectedly failed: %s" msg

let test_compile_accepts_empty_alternatives () =
  List.iter
    (fun pattern ->
       match Ecma_regex.compile pattern with
       | Ok _ -> ()
       | Error msg ->
         Alcotest.failf "empty alternative pattern %S unexpectedly failed: %s"
           pattern msg)
    [ ""; "()"; "abc()?"; "a|"; "|a"; "(?:)" ]

let test_compile_rejects_invalid_quantifier_range () =
  match Ecma_regex.compile ".{2,1}" with
  | Error _ -> ()
  | Ok _ -> Alcotest.fail "invalid quantifier range unexpectedly succeeded"

let test_compile_rejects_repeated_quantifier () =
  match Ecma_regex.compile "x{1}{1,}" with
  | Error _ -> ()
  | Ok _ -> Alcotest.fail "repeated quantifier unexpectedly succeeded"

let test_compile_accepts_negative_lookahead () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags ".B(?!A)" with
    | Ok _ -> ()
    | Error msg -> Alcotest.failf "negative lookahead unexpectedly failed: %s" msg

let test_compile_rejects_unicode_quantified_lookahead () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    List.iter
      (fun pattern ->
         match Ecma_regex.compile ~flags pattern with
         | Error _ -> ()
         | Ok _ ->
           Alcotest.failf "unicode quantified lookahead %S unexpectedly succeeded"
             pattern)
      [ "(?=.)*"; "(?!.){1,2}?" ]

let test_compile_accepts_hex_escape () =
  match Ecma_regex.compile "\\xB5" with
  | Ok _ -> ()
  | Error msg -> Alcotest.failf "hex escape unexpectedly failed: %s" msg

let test_compile_accepts_empty_character_class () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "[]" with
    | Ok _ -> ()
    | Error msg ->
      Alcotest.failf "empty character class unexpectedly failed: %s" msg

let test_compile_accepts_escaped_hyphen_in_unicode_class () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "[A\\-Z]+" with
    | Ok _ -> ()
    | Error msg ->
      Alcotest.failf
        "escaped hyphen in unicode character class unexpectedly failed: %s"
        msg

let test_compile_rejects_invalid_character_class_range () =
  match Ecma_regex.compile "^[z-a]$" with
  | Error _ -> ()
  | Ok _ -> Alcotest.fail "invalid character class range unexpectedly succeeded"

let test_compile_accepts_unicode_class_set_syntax_char () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "[(]" with
    | Ok _ -> ()
    | Error msg ->
      Alcotest.failf "unicode class syntax char unexpectedly failed: %s" msg

let test_compile_rejects_unicode_sets_class_syntax_char () =
  match Ecma_regex.flags_of_string "v" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "[(]" with
    | Error _ -> ()
    | Ok _ ->
      Alcotest.fail "unicodeSets class syntax char unexpectedly succeeded"

let test_compile_rejects_unicode_sets_reserved_double_punctuator () =
  match Ecma_regex.flags_of_string "v" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "[&&]" with
    | Error _ -> ()
    | Ok _ ->
      Alcotest.fail
        "unicodeSets reserved double punctuator unexpectedly succeeded"

let test_compile_rejects_unicode_class_escape_range_endpoint () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    List.iter
      (fun pattern ->
         match Ecma_regex.compile ~flags pattern with
         | Error _ -> ()
         | Ok _ ->
           Alcotest.failf
             "unicode class escape range endpoint %S unexpectedly succeeded"
             pattern)
      ([ "[\\d-a]"; "[a-\\d]" ]
       @ [ "[\\p{Hex}-a]"; "[a-\\p{Hex}]"; "[--\\p{Hex}]" ])

let test_compile_rejects_invalid_hex_escape () =
  match Ecma_regex.compile "\\xG5" with
  | Error _ -> ()
  | Ok _ -> Alcotest.fail "invalid hex escape unexpectedly succeeded"

let test_compile_accepts_decimal_escape () =
  match Ecma_regex.compile "(z\\1){3}" with
  | Ok _ -> ()
  | Error msg -> Alcotest.failf "decimal escape unexpectedly failed: %s" msg

let test_compile_rejects_invalid_unicode_decimal_escape () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "\\2" with
    | Error _ -> ()
    | Ok _ -> Alcotest.fail "invalid unicode decimal escape unexpectedly succeeded"

let test_compile_accepts_valid_unicode_decimal_escape () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "(a)\\1" with
    | Ok _ -> ()
    | Error msg ->
      Alcotest.failf "valid unicode decimal escape unexpectedly failed: %s" msg

let test_compile_rejects_unicode_octal_escape () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    List.iter
      (fun pattern ->
         match Ecma_regex.compile ~flags pattern with
         | Error _ -> ()
         | Ok _ ->
           Alcotest.failf "unicode octal escape %S unexpectedly succeeded"
             pattern)
      [ "\\00"; "[\\1]"; "[\\00]" ]

let test_compile_accepts_supported_unicode_property_escape () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    List.iter
      (fun pattern ->
         match Ecma_regex.compile ~flags pattern with
         | Ok _ -> ()
         | Error msg ->
           Alcotest.failf
             "supported unicode property escape %S unexpectedly failed: %s"
             pattern msg)
      [ "\\p{Script=Latin}"; "\\P{Script=Latin}"; "\\p{Letter}" ]

let test_compile_rejects_unsupported_unicode_property_escape () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    List.iter
      (fun pattern ->
         match Ecma_regex.compile ~flags pattern with
         | Error _ -> ()
         | Ok _ ->
           Alcotest.failf
             "unsupported unicode property escape %S unexpectedly succeeded"
             pattern)
      [
        "\\p{}";
        "\\p{ASCII=F}";
        "\\p{Script=}";
        "\\p{Script=FooBarBazInvalid}";
        "\\p{UnknownBinaryProperty}";
      ]

let test_compile_accepts_unicode_sets_intersection () =
  match Ecma_regex.flags_of_string "v" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "[\\p{Script=Latin}&&\\p{Letter}]" with
    | Ok _ -> ()
    | Error msg ->
      Alcotest.failf "unicodeSets intersection unexpectedly failed: %s" msg

let test_compile_accepts_modifiers_group () =
  List.iter
    (fun pattern ->
       match Ecma_regex.compile pattern with
       | Ok _ -> ()
       | Error msg ->
         Alcotest.failf "modifiers group %S unexpectedly failed: %s" pattern msg)
    [ "(?i:a)"; "(?m:a)"; "(?s:a)"; "(?i-m:a)" ]

let check_flags_ok source =
  match Ecma_regex.flags_of_string source with
  | Ok _ -> ()
  | Error msg -> Alcotest.failf "flags %S unexpectedly failed: %s" source msg

let check_flags_error source =
  match Ecma_regex.flags_of_string source with
  | Error _ -> ()
  | Ok _ -> Alcotest.failf "flags %S unexpectedly succeeded" source

let test_flags_of_string_accepts_ecmascript_flags () =
  List.iter check_flags_ok [
    "";
    "d";
    "g";
    "i";
    "m";
    "s";
    "u";
    "v";
    "y";
    "dgimsuy";
  ]

let test_flags_of_string_rejects_duplicates () =
  List.iter check_flags_error [
    "gg";
    "dd";
    "ii";
    "mm";
    "ss";
    "uu";
    "vv";
    "yy";
  ]

let test_flags_of_string_rejects_unknown_flags () =
  List.iter check_flags_error [
    "a";
    "z";
    "guq";
  ]

let test_flags_of_string_rejects_unicode_mode_conflict () =
  List.iter check_flags_error [
    "uv";
    "vu";
  ]

let test_regexp_literal_of_string_returns_flag_text () =
  match Ecma_regex.regexp_literal_of_string "/a\\/b/dy" with
  | Error msg -> Alcotest.failf "literal unexpectedly failed: %s" msg
  | Ok literal ->
    Alcotest.(check string) "pattern text" "a\\/b" literal.pattern_text;
    Alcotest.(check string) "flag text" "dy" literal.flag_text

let test_regexp_literal_of_string_respects_character_class_slash () =
  match Ecma_regex.regexp_literal_of_string "/[a/]/su" with
  | Error msg -> Alcotest.failf "literal unexpectedly failed: %s" msg
  | Ok literal ->
    Alcotest.(check string) "pattern text" "[a/]" literal.pattern_text;
    Alcotest.(check string) "flag text" "su" literal.flag_text

let test_regexp_literal_of_string_rejects_invalid_literals () =
  List.iter
    (fun source ->
       match Ecma_regex.regexp_literal_of_string source with
       | Error _ -> ()
       | Ok _ -> Alcotest.failf "literal %S unexpectedly succeeded" source)
    [ "a/g"; "/abc"; "/abc/gg"; "/a\n/g"; "/\\\n/" ]

let compile_or_fail ?flags pattern =
  match Ecma_regex.compile ?flags pattern with
  | Ok regexp -> regexp
  | Error msg -> Alcotest.failf "compile %S failed: %s" pattern msg

let flags_or_fail source =
  match Ecma_regex.flags_of_string source with
  | Ok flags -> flags
  | Error msg -> Alcotest.failf "flags %S failed: %s" source msg

let check_match_result name expected_start expected_end expected_text
    (result : Ecma_regex.match_result) =
  Alcotest.(check int)
    (name ^ " start_index")
    expected_start
    result.start_index;
  Alcotest.(check int) (name ^ " end_index") expected_end result.end_index;
  Alcotest.(check string) (name ^ " matched_text") expected_text
    result.matched_text

let js_string_of_utf16_units_or_fail units =
  match Ecma_regex.js_string_of_utf16_code_units units with
  | Ok value -> value
  | Error msg -> Alcotest.failf "js_string_of_utf16_code_units failed: %s" msg

let check_js_match_result name expected_start expected_end expected_units
    (result : Ecma_regex.js_match_result) =
  Alcotest.(check int)
    (name ^ " start_index")
    expected_start
    result.js_start_index;
  Alcotest.(check int) (name ^ " end_index") expected_end
    result.js_end_index;
  Alcotest.(check (list int))
    (name ^ " matched UTF-16 units")
    expected_units
    (Ecma_regex.js_string_to_utf16_code_units result.js_matched_text)

let check_js_capture name expected_index expected_start expected_end expected_units
    (capture : Ecma_regex.js_capture) =
  Alcotest.(check int)
    (name ^ " capture index")
    expected_index
    capture.js_capture_index;
  Alcotest.(check (option int))
    (name ^ " capture start")
    expected_start
    capture.js_capture_start_index;
  Alcotest.(check (option int))
    (name ^ " capture end")
    expected_end
    capture.js_capture_end_index;
  let actual_units =
    Option.map Ecma_regex.js_string_to_utf16_code_units capture.js_capture_text
  in
  Alcotest.(check (option (list int)))
    (name ^ " capture UTF-16 units")
    expected_units
    actual_units

let check_js_named_capture name expected_name expected_capture
    (named_capture : Ecma_regex.js_named_capture) =
  Alcotest.(check string)
    (name ^ " capture name")
    expected_name
    named_capture.js_named_capture_name;
  expected_capture named_capture.js_named_capture

let test_search_matches_literal_atom () =
  let regexp = compile_or_fail "a" in
  Alcotest.(check bool) "literal found" true (Ecma_regex.search regexp "xxa");
  Alcotest.(check bool) "literal absent" false (Ecma_regex.search regexp "bbb")

let test_search_matches_concatenation () =
  let regexp = compile_or_fail "ab" in
  Alcotest.(check bool) "concat found" true (Ecma_regex.search regexp "xxabyy");
  Alcotest.(check bool) "concat order matters" false
    (Ecma_regex.search regexp "acb")

let test_exec_returns_match_result () =
  let regexp = compile_or_fail "ab" in
  match Ecma_regex.exec regexp "xxabyy" with
  | None -> Alcotest.fail "exec unexpectedly returned None"
  | Some result ->
    Alcotest.(check int) "start_index" 2 result.start_index;
    Alcotest.(check int) "end_index" 4 result.end_index;
    Alcotest.(check string) "matched_text" "ab" result.matched_text

let test_exec_reports_utf16_indices_for_unicode_non_bmp_literal () =
  let grinning_face = "\xF0\x9F\x98\x80" in
  let cases =
    [
      ("u literal", "u", "\\u{1F600}", "a" ^ grinning_face ^ "b", 1, 3, grinning_face);
      ("v literal", "v", "\\u{1F600}", "a" ^ grinning_face ^ "b", 1, 3, grinning_face);
      ("u class", "u", "[\\u{1F600}]", "a" ^ grinning_face ^ "b", 1, 3, grinning_face);
      ("v class", "v", "[\\u{1F600}]", "a" ^ grinning_face ^ "b", 1, 3, grinning_face);
      ("u lookbehind", "u", "(?<=\\u{1F600})a", grinning_face ^ "a", 2, 3, "a");
      ("u ascii after non-BMP", "u", "a", grinning_face ^ "a", 2, 3, "a");
    ]
  in
  List.iter
    (fun (name, flag_source, pattern, input, expected_start, expected_end, expected_text) ->
       let flags = flags_or_fail flag_source in
       let regexp = compile_or_fail ~flags pattern in
       match Ecma_regex.exec regexp input with
       | None -> Alcotest.failf "%s unexpectedly returned None" name
       | Some result ->
         Alcotest.(check int)
           (name ^ " start_index")
           expected_start
           result.start_index;
         Alcotest.(check int)
           (name ^ " end_index")
           expected_end
           result.end_index;
         Alcotest.(check string)
           (name ^ " matched_text")
         expected_text
         result.matched_text)
    cases

let test_unicode_raw_non_bmp_literal_quantifier_anchors () =
  let flags = flags_or_fail "u" in
  let dragon = "\xF0\x9F\x90\xB2" in
  let other_dragon = "\xF0\x9F\x90\x89" in
  let regexp = compile_or_fail ~flags ("^" ^ dragon ^ "*$") in
  let cases =
    [
      ("empty", "", true);
      ("single", dragon, true);
      ("two", dragon ^ dragon, true);
      ("other non-BMP", other_dragon, false);
      ("two other non-BMP", other_dragon ^ other_dragon, false);
      ("ASCII", "D", false);
      ("two ASCII", "DD", false);
    ]
  in
  List.iter
    (fun (name, input, expected) ->
       Alcotest.(check bool)
         name
         expected
         (Ecma_regex.search regexp input))
    cases

let test_unicode_dot_consumes_non_bmp_code_point () =
  let flags = flags_or_fail "u" in
  let grinning_face = "\xF0\x9F\x98\x80" in
  let regexp = compile_or_fail ~flags "^.$" in
  match Ecma_regex.exec regexp grinning_face with
  | None -> Alcotest.fail "unicode dot unexpectedly returned None"
  | Some result ->
    Alcotest.(check int) "start_index" 0 result.start_index;
    Alcotest.(check int) "end_index" 2 result.end_index;
    Alcotest.(check string) "matched_text" grinning_face result.matched_text

let test_unicode_dot_uses_code_point_line_terminators () =
  let line_separator = "\xE2\x80\xA8" in
  let unicode_flags = flags_or_fail "u" in
  let dot = compile_or_fail ~flags:unicode_flags "^.$" in
  Alcotest.(check bool) "unicode dot excludes U+2028" true
    (Option.is_none (Ecma_regex.exec dot line_separator));
  let dot_all_flags = flags_or_fail "su" in
  let dot_all = compile_or_fail ~flags:dot_all_flags "^.$" in
  match Ecma_regex.exec dot_all line_separator with
  | None -> Alcotest.fail "unicode dotAll unexpectedly returned None"
  | Some result ->
    Alcotest.(check int) "start_index" 0 result.start_index;
    Alcotest.(check int) "end_index" 1 result.end_index;
    Alcotest.(check string) "matched_text" line_separator result.matched_text

let test_unicode_search_does_not_probe_inside_non_bmp_utf8 () =
  let grinning_face = "\xF0\x9F\x98\x80" in
  let cases =
    [
      ("u literal", "u", "\\u{9F}", grinning_face, None);
      ("v literal", "v", "\\u{9F}", grinning_face, None);
      ("u class", "u", "[\\u{9F}]", grinning_face, None);
      ("v class", "v", "[\\u{9F}]", grinning_face, None);
      ( "u alternation advances to next code point",
        "u",
        "\\u{9F}|a",
        grinning_face ^ "a",
        Some (2, 3, "a") );
      ( "v alternation advances to next code point",
        "v",
        "\\u{9F}|a",
        grinning_face ^ "a",
        Some (2, 3, "a") );
    ]
  in
  List.iter
    (fun (name, flag_source, pattern, input, expected) ->
       let flags = flags_or_fail flag_source in
       let regexp = compile_or_fail ~flags pattern in
       match expected, Ecma_regex.exec regexp input with
       | None, None -> ()
       | None, Some result ->
         Alcotest.failf "%s unexpectedly matched %d..%d %S"
           name result.start_index result.end_index result.matched_text
       | Some (expected_start, expected_end, expected_text), Some result ->
         Alcotest.(check int)
           (name ^ " start_index")
           expected_start
           result.start_index;
         Alcotest.(check int)
           (name ^ " end_index")
           expected_end
           result.end_index;
         Alcotest.(check string)
           (name ^ " matched_text")
           expected_text
           result.matched_text
       | Some _, None -> Alcotest.failf "%s unexpectedly returned None" name)
    cases

let test_sticky_exec_does_not_search_past_initial_index () =
  let sticky_flags = flags_or_fail "y" in
  let regexp = compile_or_fail ~flags:sticky_flags "a" in
  Alcotest.(check bool) "sticky failure at index 0" true
    (Option.is_none (Ecma_regex.exec regexp "ba"));
  let unicode_sticky_flags = flags_or_fail "uy" in
  let grinning_face = "\xF0\x9F\x98\x80" in
  let unicode_regexp =
    compile_or_fail ~flags:unicode_sticky_flags "\\u{9F}|a"
  in
  Alcotest.(check bool) "unicode sticky does not advance after failure" true
    (Option.is_none (Ecma_regex.exec unicode_regexp (grinning_face ^ "a")))

let test_global_instance_updates_last_index () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "a" in
  let instance = Ecma_regex.instance regexp in
  Alcotest.(check int) "initial last_index" 0
    (Ecma_regex.last_index instance);
  (match Ecma_regex.exec_instance instance "baac" with
   | None -> Alcotest.fail "first global exec unexpectedly returned None"
   | Some result ->
     Alcotest.(check int) "first start_index" 1 result.start_index;
     Alcotest.(check int) "first end_index" 2 result.end_index;
     Alcotest.(check string) "first matched_text" "a" result.matched_text);
  Alcotest.(check int) "last_index after first match" 2
    (Ecma_regex.last_index instance);
  (match Ecma_regex.exec_instance instance "baac" with
   | None -> Alcotest.fail "second global exec unexpectedly returned None"
   | Some result ->
     Alcotest.(check int) "second start_index" 2 result.start_index;
     Alcotest.(check int) "second end_index" 3 result.end_index;
     Alcotest.(check string) "second matched_text" "a" result.matched_text);
  Alcotest.(check int) "last_index after second match" 3
    (Ecma_regex.last_index instance);
  Alcotest.(check bool) "global failure at tail" true
    (Option.is_none (Ecma_regex.exec_instance instance "baac"));
  Alcotest.(check int) "last_index reset after global failure" 0
    (Ecma_regex.last_index instance)

let test_unicode_global_instance_uses_utf16_last_index () =
  let flags = flags_or_fail "gu" in
  let grinning_face = "\xF0\x9F\x98\x80" in
  let regexp = compile_or_fail ~flags "a" in
  let instance = Ecma_regex.instance regexp in
  (match Ecma_regex.exec_instance instance (grinning_face ^ "a") with
   | None -> Alcotest.fail "unicode global exec unexpectedly returned None"
   | Some result ->
     Alcotest.(check int) "start_index" 2 result.start_index;
     Alcotest.(check int) "end_index" 3 result.end_index;
     Alcotest.(check string) "matched_text" "a" result.matched_text);
  Alcotest.(check int) "last_index after non-BMP prefix" 3
    (Ecma_regex.last_index instance)

let test_sticky_instance_uses_explicit_last_index () =
  let flags = flags_or_fail "y" in
  let regexp = compile_or_fail ~flags "a" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 1;
  (match Ecma_regex.exec_instance instance "ba" with
   | None -> Alcotest.fail "sticky exec at explicit last_index returned None"
   | Some result ->
     Alcotest.(check int) "start_index" 1 result.start_index;
     Alcotest.(check int) "end_index" 2 result.end_index;
     Alcotest.(check string) "matched_text" "a" result.matched_text);
  Alcotest.(check int) "last_index after sticky success" 2
    (Ecma_regex.last_index instance);
  Alcotest.(check bool) "sticky tail failure" true
    (Option.is_none (Ecma_regex.exec_instance instance "ba"));
  Alcotest.(check int) "last_index reset after sticky failure" 0
    (Ecma_regex.last_index instance)

let test_instance_out_of_bounds_last_index_resets () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "a" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 3;
  Alcotest.(check bool) "out-of-bounds global exec" true
    (Option.is_none (Ecma_regex.exec_instance instance "a"));
  Alcotest.(check int) "last_index reset after out-of-bounds" 0
    (Ecma_regex.last_index instance)

let test_non_global_instance_does_not_mutate_last_index () =
  let regexp = compile_or_fail "a" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 2;
  (match Ecma_regex.exec_instance instance "ba" with
   | None -> Alcotest.fail "non-global exec unexpectedly returned None"
   | Some result ->
     Alcotest.(check int) "start_index" 1 result.start_index;
     Alcotest.(check int) "end_index" 2 result.end_index;
     Alcotest.(check string) "matched_text" "a" result.matched_text);
  Alcotest.(check int) "non-global last_index unchanged" 2
    (Ecma_regex.last_index instance)

let test_global_iterator_advances_after_empty_match () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  let iterator = Ecma_regex.iter_matches instance "ab" in
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "first global iterator step returned None"
   | Some result -> check_match_result "first empty match" 0 0 "" result);
  Alcotest.(check int) "last_index after first empty match" 1
    (Ecma_regex.last_index instance);
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "second global iterator step returned None"
   | Some result -> check_match_result "second empty match" 1 1 "" result);
  Alcotest.(check int) "last_index after second empty match" 2
    (Ecma_regex.last_index instance);
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "third global iterator step returned None"
   | Some result -> check_match_result "third empty match" 2 2 "" result);
  Alcotest.(check int) "last_index after terminal empty match" 3
    (Ecma_regex.last_index instance);
  Alcotest.(check bool) "global iterator done after out-of-bounds step" true
    (Option.is_none (Ecma_regex.next_match iterator));
  Alcotest.(check int) "last_index reset after iterator exhaustion" 0
    (Ecma_regex.last_index instance)

let test_unicode_global_iterator_advances_non_bmp_empty_match () =
  let flags = flags_or_fail "gu" in
  let grinning_face = "\xF0\x9F\x98\x80" in
  let input = grinning_face ^ "a" in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  let iterator = Ecma_regex.iter_matches instance input in
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "first unicode iterator step returned None"
   | Some result -> check_match_result "unicode empty at start" 0 0 "" result);
  Alcotest.(check int) "unicode last_index after non-BMP advance" 2
    (Ecma_regex.last_index instance);
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "second unicode iterator step returned None"
   | Some result ->
     check_match_result "unicode empty after non-BMP" 2 2 "" result);
  Alcotest.(check int) "unicode last_index after ASCII advance" 3
    (Ecma_regex.last_index instance);
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "terminal unicode iterator step returned None"
   | Some result -> check_match_result "unicode terminal empty" 3 3 "" result);
  Alcotest.(check int) "unicode last_index after terminal empty match" 4
    (Ecma_regex.last_index instance);
  Alcotest.(check bool) "unicode iterator done after out-of-bounds step" true
    (Option.is_none (Ecma_regex.next_match iterator));
  Alcotest.(check int) "unicode last_index reset after exhaustion" 0
    (Ecma_regex.last_index instance)

let test_global_sticky_iterator_advances_after_empty_match () =
  let flags = flags_or_fail "gy" in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  let iterator = Ecma_regex.iter_matches instance "ab" in
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "first global-sticky iterator step returned None"
   | Some result ->
     check_match_result "first global-sticky empty match" 0 0 "" result);
  Alcotest.(check int) "last_index after first global-sticky empty match" 1
    (Ecma_regex.last_index instance);
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "second global-sticky iterator step returned None"
   | Some result ->
     check_match_result "second global-sticky empty match" 1 1 "" result);
  Alcotest.(check int) "last_index after second global-sticky empty match" 2
    (Ecma_regex.last_index instance);
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "third global-sticky iterator step returned None"
   | Some result ->
     check_match_result "third global-sticky empty match" 2 2 "" result);
  Alcotest.(check int) "last_index after terminal global-sticky empty match" 3
    (Ecma_regex.last_index instance);
  Alcotest.(check bool) "global-sticky iterator done" true
    (Option.is_none (Ecma_regex.next_match iterator));
  Alcotest.(check int) "global-sticky last_index reset after exhaustion" 0
    (Ecma_regex.last_index instance)

let test_non_global_iterator_is_done_after_first_match () =
  let regexp = compile_or_fail "" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 2;
  let iterator = Ecma_regex.iter_matches instance "ab" in
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "non-global iterator returned None"
   | Some result -> check_match_result "non-global iterator match" 0 0 "" result);
  Alcotest.(check int) "non-global iterator keeps last_index" 2
    (Ecma_regex.last_index instance);
  Alcotest.(check bool) "non-global iterator is done after first match" true
    (Option.is_none (Ecma_regex.next_match iterator));
  Alcotest.(check int) "done non-global iterator keeps last_index" 2
    (Ecma_regex.last_index instance)

let test_sticky_non_global_iterator_is_done_after_first_match () =
  let flags = flags_or_fail "y" in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  let iterator = Ecma_regex.iter_matches instance "ab" in
  (match Ecma_regex.next_match iterator with
   | None -> Alcotest.fail "sticky non-global iterator returned None"
   | Some result ->
     check_match_result "sticky non-global iterator match" 0 0 "" result);
  Alcotest.(check int) "sticky non-global last_index after empty match" 0
    (Ecma_regex.last_index instance);
  Alcotest.(check bool) "sticky non-global iterator done" true
    (Option.is_none (Ecma_regex.next_match iterator));
  Alcotest.(check int) "done sticky non-global last_index unchanged" 0
    (Ecma_regex.last_index instance)

let test_js_string_rejects_invalid_utf16_units () =
  let cases = [ [ -1 ]; [ 0x10000 ]; [ 0x41; 0x110000 ] ] in
  List.iter
    (fun units ->
       match Ecma_regex.js_string_of_utf16_code_units units with
       | Error _ -> ()
       | Ok _ ->
         Alcotest.failf "invalid UTF-16 units unexpectedly accepted")
    cases

let test_js_string_lone_surrogate_literals_match_code_units () =
  let high_surrogate = 0xD800 in
  let input = js_string_of_utf16_units_or_fail [ high_surrogate ] in
  let cases = [ ("non-unicode", "", "\\uD800"); ("unicode", "u", "\\uD800") ] in
  List.iter
    (fun (name, flag_source, pattern) ->
       let flags = flags_or_fail flag_source in
       let regexp = compile_or_fail ~flags pattern in
       match Ecma_regex.exec_js regexp input with
       | None -> Alcotest.failf "%s lone surrogate returned None" name
       | Some result ->
         check_js_match_result name 0 1 [ high_surrogate ] result)
    cases

let test_js_string_unicode_surrogate_pair_matches_code_point () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ] in
  let regexp = compile_or_fail ~flags "\\u{1F600}" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "unicode surrogate pair returned None"
  | Some result -> check_js_match_result "surrogate pair" 0 2 [ high; low ] result

let test_js_string_non_unicode_can_match_surrogate_half () =
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low ] in
  let regexp = compile_or_fail "\\uD83D" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "non-unicode high surrogate returned None"
  | Some result -> check_js_match_result "high surrogate" 0 1 [ high ] result

let test_js_string_unicode_empty_iterator_advances_over_surrogate_pair () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ] in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  let iterator = Ecma_regex.iter_matches_js instance input in
  (match Ecma_regex.next_match_js iterator with
   | None -> Alcotest.fail "first raw UTF-16 iterator step returned None"
   | Some result -> check_js_match_result "raw UTF-16 empty at start" 0 0 [] result);
  Alcotest.(check int) "last_index after surrogate pair advance" 2
    (Ecma_regex.last_index instance)

let test_js_string_unicode_empty_iterator_inside_surrogate_pair () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ] in
  let regexp = compile_or_fail ~flags "" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 1;
  let iterator = Ecma_regex.iter_matches_js instance input in
  (match Ecma_regex.next_match_js iterator with
   | None -> Alcotest.fail "inside-surrogate iterator step returned None"
   | Some result ->
     check_js_match_result "empty at low surrogate code unit" 1 1 [] result);
  Alcotest.(check int) "last_index advances one code unit from low surrogate" 2
    (Ecma_regex.last_index instance)

let test_js_string_non_unicode_dot_consumes_one_code_unit () =
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low ] in
  let regexp = compile_or_fail "." in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "non-unicode dot returned None"
  | Some result -> check_js_match_result "non-unicode dot" 0 1 [ high ] result

let test_js_string_non_unicode_class_escape_consumes_one_code_unit () =
  let high = 0xD83D in
  let input = js_string_of_utf16_units_or_fail [ high ] in
  let regexp = compile_or_fail "\\D" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "non-unicode class escape returned None"
  | Some result -> check_js_match_result "non-unicode \\D" 0 1 [ high ] result

let test_js_string_surrogate_pair_capture_and_backreference () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low; high; low ] in
  let regexp = compile_or_fail ~flags "(\\u{1F600})\\1" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "unicode surrogate pair backreference returned None"
  | Some result ->
    check_js_match_result "unicode surrogate pair backreference" 0 4
      [ high; low; high; low ]
      result

let test_js_match_result_exposes_numbered_captures_as_utf16_slices () =
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low ] in
  let regexp = compile_or_fail "(\\uD83D)(\\uDE00)" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "non-unicode surrogate captures returned None"
  | Some result ->
    check_js_match_result "non-unicode surrogate captures" 0 2 [ high; low ]
      result;
    Alcotest.(check int)
      "numbered capture count"
      2
      (List.length result.js_captures);
    (match result.js_captures with
     | [ high_capture; low_capture ] ->
       check_js_capture "high surrogate capture" 1 (Some 0) (Some 1)
         (Some [ high ])
         high_capture;
       check_js_capture "low surrogate capture" 2 (Some 1) (Some 2)
         (Some [ low ])
         low_capture
     | _ -> Alcotest.fail "unexpected numbered capture shape")

let test_js_match_result_exposes_unicode_capture_as_surrogate_pair_slice () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low ] in
  let regexp = compile_or_fail ~flags "(\\u{1F600})" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "unicode capture returned None"
  | Some result ->
    check_js_match_result "unicode capture" 0 2 [ high; low ] result;
    (match result.js_captures with
     | [ capture ] ->
       check_js_capture "unicode surrogate-pair capture" 1 (Some 0) (Some 2)
         (Some [ high; low ])
         capture
     | _ -> Alcotest.fail "unexpected unicode capture shape")

let test_js_match_result_exposes_undefined_capture () =
  let input = js_string_of_utf16_units_or_fail [ Char.code 'b' ] in
  let regexp = compile_or_fail "(a)?b" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "optional capture match returned None"
  | Some result ->
    check_js_match_result "optional capture full match" 0 1 [ Char.code 'b' ]
      result;
    (match result.js_captures with
     | [ capture ] ->
       check_js_capture "undefined optional capture" 1 None None None capture
     | _ -> Alcotest.fail "unexpected optional capture shape")

let test_js_match_result_exposes_named_captures () =
  let input = js_string_of_utf16_units_or_fail [ Char.code 'a'; Char.code 'b' ] in
  let regexp = compile_or_fail "(?<first>a)(b)" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "named capture match returned None"
  | Some result ->
    check_js_match_result "named capture full match" 0 2
      [ Char.code 'a'; Char.code 'b' ]
      result;
    Alcotest.(check int)
      "numbered captures include named and unnamed groups"
      2
      (List.length result.js_captures);
    (match result.js_named_captures with
     | [ named_capture ] ->
       check_js_named_capture "first named capture" "first"
         (check_js_capture "first named capture value" 1 (Some 0) (Some 1)
            (Some [ Char.code 'a' ]))
         named_capture
     | _ -> Alcotest.fail "unexpected named capture shape")

let test_js_match_result_exposes_instance_and_iterator_captures () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail
      [ high; low; Char.code 'x'; high; low ]
  in
  let regexp = compile_or_fail ~flags "(\\u{1F600})" in
  let instance = Ecma_regex.instance regexp in
  (match Ecma_regex.exec_instance_js instance input with
   | None -> Alcotest.fail "instance capture match returned None"
   | Some result ->
     check_js_match_result "instance first capture full match" 0 2
       [ high; low ]
       result;
     (match result.js_captures with
      | [ capture ] ->
        check_js_capture "instance first capture" 1 (Some 0) (Some 2)
          (Some [ high; low ])
          capture
      | _ -> Alcotest.fail "unexpected instance capture shape"));
  let iterator = Ecma_regex.iter_matches_js instance input in
  match Ecma_regex.next_match_js iterator with
  | None -> Alcotest.fail "iterator capture match returned None"
  | Some result ->
    check_js_match_result "iterator second capture full match" 3 5
      [ high; low ]
      result;
    (match result.js_captures with
     | [ capture ] ->
       check_js_capture "iterator second capture" 1 (Some 3) (Some 5)
         (Some [ high; low ])
         capture
     | _ -> Alcotest.fail "unexpected iterator capture shape")

let test_js_string_unicode_lookbehind_crosses_surrogate_pair () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ] in
  let regexp = compile_or_fail ~flags "(?<=\\u{1F600})a" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "unicode lookbehind after surrogate pair returned None"
  | Some result ->
    check_js_match_result "unicode lookbehind after surrogate pair" 2 3
      [ Char.code 'a' ]
      result

let test_js_string_character_classes_match_raw_utf16 () =
  let high = 0xD83D in
  let low = 0xDE00 in
  let pair = js_string_of_utf16_units_or_fail [ high; low ] in
  let unicode_flags = flags_or_fail "u" in
  let unicode_class = compile_or_fail ~flags:unicode_flags "[\\u{1F600}]" in
  (match Ecma_regex.exec_js unicode_class pair with
   | None -> Alcotest.fail "unicode class did not match surrogate pair"
   | Some result ->
     check_js_match_result "unicode class surrogate pair" 0 2 [ high; low ]
       result);
  let high_only = js_string_of_utf16_units_or_fail [ high ] in
  let non_unicode_class = compile_or_fail "[\\uD83D]" in
  match Ecma_regex.exec_js non_unicode_class high_only with
  | None -> Alcotest.fail "non-unicode class did not match high surrogate"
  | Some result ->
    check_js_match_result "non-unicode class high surrogate" 0 1 [ high ]
      result

let test_js_string_anchors_use_utf16_boundaries () =
  let high = 0xD83D in
  let input = js_string_of_utf16_units_or_fail [ high ] in
  let regexp = compile_or_fail "^\\uD83D$" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "anchors around high surrogate returned None"
  | Some result -> check_js_match_result "anchors high surrogate" 0 1 [ high ] result

let test_js_string_unicode_class_escape_consumes_surrogate_pair () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low ] in
  let regexp = compile_or_fail ~flags "\\D" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "unicode \\D over surrogate pair returned None"
  | Some result ->
    check_js_match_result "unicode \\D surrogate pair" 0 2 [ high; low ] result

let test_js_string_unicode_simple_class_consumes_surrogate_pair () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low ] in
  let regexp = compile_or_fail ~flags "[^a]" in
  match Ecma_regex.exec_js regexp input with
  | None -> Alcotest.fail "unicode [^a] over surrogate pair returned None"
  | Some result ->
    check_js_match_result "unicode [^a] surrogate pair" 0 2 [ high; low ] result

let test_js_string_ecma_whitespace_class_escapes () =
  let line_separator = 0x2028 in
  let no_break_space = 0x00A0 in
  let line_input = js_string_of_utf16_units_or_fail [ line_separator ] in
  let nbsp_input = js_string_of_utf16_units_or_fail [ no_break_space ] in
  let space = compile_or_fail "\\s" in
  (match Ecma_regex.exec_js space line_input with
   | None -> Alcotest.fail "\\s did not match U+2028"
   | Some result ->
     check_js_match_result "\\s line separator" 0 1 [ line_separator ] result);
  let non_space = compile_or_fail "\\S" in
  Alcotest.(check bool) "\\S rejects U+2028" true
    (Option.is_none (Ecma_regex.exec_js non_space line_input));
  let class_space = compile_or_fail "[\\s]" in
  match Ecma_regex.exec_js class_space nbsp_input with
  | None -> Alcotest.fail "[\\s] did not match U+00A0"
  | Some result ->
    check_js_match_result "[\\s] no-break space" 0 1 [ no_break_space ] result

let test_js_string_multiline_anchors_use_ecma_line_terminators () =
  let flags = flags_or_fail "m" in
  let line_separator = 0x2028 in
  let paragraph_separator = 0x2029 in
  let start_input =
    js_string_of_utf16_units_or_fail [ line_separator; Char.code 'a' ]
  in
  let start_regexp = compile_or_fail ~flags "^a" in
  (match Ecma_regex.exec_js start_regexp start_input with
   | None -> Alcotest.fail "^ did not match after U+2028 in multiline mode"
   | Some result ->
     check_js_match_result "multiline start after U+2028" 1 2
       [ Char.code 'a' ]
       result);
  let end_input =
    js_string_of_utf16_units_or_fail [ Char.code 'a'; paragraph_separator ]
  in
  let end_regexp = compile_or_fail ~flags "a$" in
  match Ecma_regex.exec_js end_regexp end_input with
  | None -> Alcotest.fail "$ did not match before U+2029 in multiline mode"
  | Some result ->
    check_js_match_result "multiline end before U+2029" 0 1 [ Char.code 'a' ]
      result

let test_js_string_word_boundary_uses_unicode_wordcharacters () =
  let flags = flags_or_fail "iu" in
  let long_s = 0x017F in
  let input = js_string_of_utf16_units_or_fail [ long_s ] in
  let word = compile_or_fail ~flags "\\w" in
  (match Ecma_regex.exec_js word input with
   | None -> Alcotest.fail "\\w did not match U+017F under iu"
   | Some result -> check_js_match_result "\\w long s" 0 1 [ long_s ] result);
  let boundary_word = compile_or_fail ~flags "\\b\\w" in
  match Ecma_regex.exec_js boundary_word input with
  | None -> Alcotest.fail "\\b\\w did not match U+017F under iu"
  | Some result -> check_js_match_result "\\b\\w long s" 0 1 [ long_s ] result

let test_exec_preserves_leftmost_alternative_result () =
  let regexp = compile_or_fail "a|aa" in
  match Ecma_regex.exec regexp "aa" with
  | None -> Alcotest.fail "exec unexpectedly returned None"
  | Some result ->
    Alcotest.(check int) "start_index" 0 result.start_index;
    Alcotest.(check int) "end_index" 1 result.end_index;
    Alcotest.(check string) "matched_text" "a" result.matched_text

let test_exec_returns_none_without_match () =
  let regexp = compile_or_fail "ab" in
  Alcotest.(check bool) "no result" true
    (Option.is_none (Ecma_regex.exec regexp "acb"))

let test_exec_matches_start_anchor () =
  let regexp = compile_or_fail "^" in
  match Ecma_regex.exec regexp "a" with
  | None -> Alcotest.fail "start anchor unexpectedly returned None"
  | Some result ->
    Alcotest.(check int) "start_index" 0 result.start_index;
    Alcotest.(check int) "end_index" 0 result.end_index;
    Alcotest.(check string) "matched_text" "" result.matched_text

let test_search_matches_start_anchor () =
  let regexp = compile_or_fail "^a" in
  Alcotest.(check bool) "match at input start" true
    (Ecma_regex.search regexp "ab");
  Alcotest.(check bool) "no unanchored later match" false
    (Ecma_regex.search regexp "ba")

let test_exec_matches_end_anchor () =
  let regexp = compile_or_fail "$" in
  match Ecma_regex.exec regexp "a" with
  | None -> Alcotest.fail "end anchor unexpectedly returned None"
  | Some result ->
    Alcotest.(check int) "start_index" 1 result.start_index;
    Alcotest.(check int) "end_index" 1 result.end_index;
    Alcotest.(check string) "matched_text" "" result.matched_text

let test_search_matches_end_anchor () =
  let regexp = compile_or_fail "a$" in
  Alcotest.(check bool) "match at input end" true
    (Ecma_regex.search regexp "ba");
  Alcotest.(check bool) "no unanchored earlier match" false
    (Ecma_regex.search regexp "ab")

let test_search_matches_dot_atom () =
  let regexp = compile_or_fail "." in
  Alcotest.(check bool) "dot matches ordinary character" true
    (Ecma_regex.search regexp "a");
  Alcotest.(check bool) "dot excludes line feed without s" false
    (Ecma_regex.search regexp "\n");
  match Ecma_regex.flags_of_string "s" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    let dot_all = compile_or_fail ~flags "." in
    Alcotest.(check bool) "dotAll includes line feed" true
      (Ecma_regex.search dot_all "\n")

let test_search_matches_character_class_atoms () =
  let regexp = compile_or_fail "[a-c]" in
  Alcotest.(check bool) "class member" true (Ecma_regex.search regexp "b");
  Alcotest.(check bool) "class non-member" false
    (Ecma_regex.search regexp "z");
  let inverted = compile_or_fail "[^a]" in
  Alcotest.(check bool) "inverted class member" true
    (Ecma_regex.search inverted "b");
  Alcotest.(check bool) "inverted class excluded" false
    (Ecma_regex.search inverted "a")

let test_search_matches_character_class_escapes () =
  let digit = compile_or_fail "\\d" in
  Alcotest.(check bool) "digit member" true (Ecma_regex.search digit "5");
  Alcotest.(check bool) "digit non-member" false
    (Ecma_regex.search digit "x");
  let non_digit = compile_or_fail "\\D" in
  Alcotest.(check bool) "non-digit rejects digit" false
    (Ecma_regex.search non_digit "5");
  let word = compile_or_fail "\\w" in
  Alcotest.(check bool) "word underscore" true (Ecma_regex.search word "_");
  let space = compile_or_fail "\\s" in
  Alcotest.(check bool) "space tab" true (Ecma_regex.search space "\t")

let test_compile_accepts_braced_unicode_escape_with_unicode_flag () =
  match Ecma_regex.flags_of_string "u" with
  | Error msg -> Alcotest.failf "flags failed: %s" msg
  | Ok flags ->
    match Ecma_regex.compile ~flags "\\u{41}" with
    | Ok _ -> ()
    | Error msg ->
      Alcotest.failf "braced unicode escape unexpectedly failed: %s" msg

let test_compile_accepts_legacy_braced_unicode_text_without_unicode_flag () =
  match Ecma_regex.compile "\\u{41}" with
  | Ok _ -> ()
  | Error msg ->
    Alcotest.failf
      "legacy non-unicode braced unicode text unexpectedly failed: %s"
      msg

let test_compile_accepts_legacy_invalid_braced_unicode_text () =
  match Ecma_regex.compile "\\u{4A}" with
  | Ok _ -> ()
  | Error msg ->
    Alcotest.failf
      "legacy non-unicode invalid braced unicode text unexpectedly failed: %s"
      msg

let test_compile_accepts_duplicate_named_groups_across_disjunction () =
  match Ecma_regex.compile "(?<a>x)|(?<a>y)" with
  | Ok _ -> ()
  | Error msg ->
    Alcotest.failf
      "duplicate named groups across disjunction unexpectedly failed: %s"
      msg

let test_compile_rejects_duplicate_named_groups_in_same_alternative () =
  match Ecma_regex.compile "(?<x>a)(?<x>b)" with
  | Error _ -> ()
  | Ok _ ->
    Alcotest.fail
      "duplicate named groups in the same alternative unexpectedly succeeded"

let test_compile_rejects_invalid_named_group_start () =
  match Ecma_regex.compile "(?<1>x)" with
  | Error _ -> ()
  | Ok _ -> Alcotest.fail "invalid named group start unexpectedly succeeded"

let test_compile_accepts_named_backreference_with_matching_group () =
  match Ecma_regex.compile "(?<name>a)\\k<name>" with
  | Ok _ -> ()
  | Error msg ->
    Alcotest.failf "matching named backreference unexpectedly failed: %s" msg

let test_compile_rejects_named_backreference_without_matching_group () =
  match Ecma_regex.compile "\\k<missing>" with
  | Error _ -> ()
  | Ok _ ->
    Alcotest.fail
      "missing named backreference target unexpectedly succeeded"

let () =
  Alcotest.run "ecma-regex" [
    ("api", [
      Alcotest.test_case "compile accepts simple literal" `Quick
        test_compile_accepts_simple_literal;
      Alcotest.test_case "compile accepts anchors" `Quick
        test_compile_accepts_anchor_syntax;
      Alcotest.test_case "compile accepts character class escape" `Quick
        test_compile_accepts_character_class_escape;
      Alcotest.test_case "compile accepts non-unicode identity escape" `Quick
        test_compile_accepts_non_unicode_identity_escape;
      Alcotest.test_case "compile rejects unicode identity escape" `Quick
        test_compile_rejects_unicode_identity_escape;
      Alcotest.test_case "compile accepts control escapes" `Quick
        test_compile_accepts_control_escapes;
      Alcotest.test_case "compile accepts control-letter escape" `Quick
        test_compile_accepts_control_letter_escape;
      Alcotest.test_case "compile accepts dot atom" `Quick
        test_compile_accepts_dot_atom;
      Alcotest.test_case "compile accepts empty alternatives" `Quick
        test_compile_accepts_empty_alternatives;
      Alcotest.test_case "compile rejects invalid quantifier range" `Quick
        test_compile_rejects_invalid_quantifier_range;
      Alcotest.test_case "compile rejects repeated quantifier" `Quick
        test_compile_rejects_repeated_quantifier;
      Alcotest.test_case "compile accepts negative lookahead" `Quick
        test_compile_accepts_negative_lookahead;
      Alcotest.test_case "compile rejects unicode quantified lookahead" `Quick
        test_compile_rejects_unicode_quantified_lookahead;
      Alcotest.test_case "compile accepts hex escape" `Quick
        test_compile_accepts_hex_escape;
      Alcotest.test_case "compile accepts empty character class" `Quick
        test_compile_accepts_empty_character_class;
      Alcotest.test_case "compile accepts escaped hyphen in unicode class" `Quick
        test_compile_accepts_escaped_hyphen_in_unicode_class;
      Alcotest.test_case "compile rejects invalid character class range" `Quick
        test_compile_rejects_invalid_character_class_range;
      Alcotest.test_case "compile accepts unicode class syntax char" `Quick
        test_compile_accepts_unicode_class_set_syntax_char;
      Alcotest.test_case "compile rejects unicodeSets class syntax char" `Quick
        test_compile_rejects_unicode_sets_class_syntax_char;
      Alcotest.test_case
        "compile rejects unicodeSets reserved double punctuator"
        `Quick
        test_compile_rejects_unicode_sets_reserved_double_punctuator;
      Alcotest.test_case
        "compile rejects unicode class escape range endpoint"
        `Quick
        test_compile_rejects_unicode_class_escape_range_endpoint;
      Alcotest.test_case "compile rejects invalid hex escape" `Quick
        test_compile_rejects_invalid_hex_escape;
      Alcotest.test_case "compile accepts decimal escape" `Quick
        test_compile_accepts_decimal_escape;
      Alcotest.test_case "compile rejects invalid unicode decimal escape" `Quick
        test_compile_rejects_invalid_unicode_decimal_escape;
      Alcotest.test_case "compile accepts valid unicode decimal escape" `Quick
        test_compile_accepts_valid_unicode_decimal_escape;
      Alcotest.test_case "compile rejects unicode octal escape" `Quick
        test_compile_rejects_unicode_octal_escape;
      Alcotest.test_case "compile accepts supported unicode property escape"
        `Quick
        test_compile_accepts_supported_unicode_property_escape;
      Alcotest.test_case "compile rejects unsupported unicode property escape"
        `Quick
        test_compile_rejects_unsupported_unicode_property_escape;
      Alcotest.test_case "compile accepts unicodeSets intersection" `Quick
        test_compile_accepts_unicode_sets_intersection;
      Alcotest.test_case "compile accepts modifiers group" `Quick
        test_compile_accepts_modifiers_group;
      Alcotest.test_case "flags accept ECMAScript flags" `Quick
        test_flags_of_string_accepts_ecmascript_flags;
      Alcotest.test_case "flags reject duplicates" `Quick
        test_flags_of_string_rejects_duplicates;
      Alcotest.test_case "flags reject unknown flags" `Quick
        test_flags_of_string_rejects_unknown_flags;
      Alcotest.test_case "flags reject unicode mode conflict" `Quick
        test_flags_of_string_rejects_unicode_mode_conflict;
      Alcotest.test_case "literal returns flag text" `Quick
        test_regexp_literal_of_string_returns_flag_text;
      Alcotest.test_case "literal respects character class slash" `Quick
        test_regexp_literal_of_string_respects_character_class_slash;
      Alcotest.test_case "literal rejects invalid literals" `Quick
        test_regexp_literal_of_string_rejects_invalid_literals;
      Alcotest.test_case "search matches literal atom" `Quick
        test_search_matches_literal_atom;
      Alcotest.test_case "search matches concatenation" `Quick
        test_search_matches_concatenation;
      Alcotest.test_case "exec returns match result" `Quick
        test_exec_returns_match_result;
      Alcotest.test_case "exec reports UTF-16 indices for unicode non-BMP literal"
        `Quick
        test_exec_reports_utf16_indices_for_unicode_non_bmp_literal;
      Alcotest.test_case
        "unicode raw non-BMP literal quantifier anchors"
        `Quick
        test_unicode_raw_non_bmp_literal_quantifier_anchors;
      Alcotest.test_case "unicode dot consumes non-BMP code point" `Quick
        test_unicode_dot_consumes_non_bmp_code_point;
      Alcotest.test_case "unicode dot uses code-point line terminators" `Quick
        test_unicode_dot_uses_code_point_line_terminators;
      Alcotest.test_case
        "unicode search does not probe inside non-BMP UTF-8 sequence"
        `Quick
        test_unicode_search_does_not_probe_inside_non_bmp_utf8;
      Alcotest.test_case "sticky exec does not search past initial index" `Quick
        test_sticky_exec_does_not_search_past_initial_index;
      Alcotest.test_case "global instance updates last_index" `Quick
        test_global_instance_updates_last_index;
      Alcotest.test_case "unicode global instance uses UTF-16 last_index" `Quick
        test_unicode_global_instance_uses_utf16_last_index;
      Alcotest.test_case "sticky instance uses explicit last_index" `Quick
        test_sticky_instance_uses_explicit_last_index;
      Alcotest.test_case "instance out-of-bounds last_index resets" `Quick
        test_instance_out_of_bounds_last_index_resets;
      Alcotest.test_case "non-global instance does not mutate last_index" `Quick
        test_non_global_instance_does_not_mutate_last_index;
      Alcotest.test_case "global iterator advances after empty match" `Quick
        test_global_iterator_advances_after_empty_match;
      Alcotest.test_case
        "unicode global iterator advances non-BMP empty match"
        `Quick
        test_unicode_global_iterator_advances_non_bmp_empty_match;
      Alcotest.test_case "global sticky iterator advances after empty match"
        `Quick
        test_global_sticky_iterator_advances_after_empty_match;
      Alcotest.test_case "non-global iterator is done after first match" `Quick
        test_non_global_iterator_is_done_after_first_match;
      Alcotest.test_case
        "sticky non-global iterator is done after first match"
        `Quick
        test_sticky_non_global_iterator_is_done_after_first_match;
      Alcotest.test_case "JS string rejects invalid UTF-16 units" `Quick
        test_js_string_rejects_invalid_utf16_units;
      Alcotest.test_case "JS string lone surrogate literals match code units"
        `Quick
        test_js_string_lone_surrogate_literals_match_code_units;
      Alcotest.test_case
        "JS string unicode surrogate pair matches code point"
        `Quick
        test_js_string_unicode_surrogate_pair_matches_code_point;
      Alcotest.test_case
        "JS string non-unicode can match surrogate half"
        `Quick
        test_js_string_non_unicode_can_match_surrogate_half;
      Alcotest.test_case
        "JS string unicode empty iterator advances over surrogate pair"
        `Quick
        test_js_string_unicode_empty_iterator_advances_over_surrogate_pair;
      Alcotest.test_case
        "JS string unicode empty iterator inside surrogate pair"
        `Quick
        test_js_string_unicode_empty_iterator_inside_surrogate_pair;
      Alcotest.test_case
        "JS string non-unicode dot consumes one code unit"
        `Quick
        test_js_string_non_unicode_dot_consumes_one_code_unit;
      Alcotest.test_case
        "JS string non-unicode class escape consumes one code unit"
        `Quick
        test_js_string_non_unicode_class_escape_consumes_one_code_unit;
      Alcotest.test_case
        "JS string surrogate pair capture and backreference"
        `Quick
        test_js_string_surrogate_pair_capture_and_backreference;
      Alcotest.test_case
        "JS match result exposes numbered captures as UTF-16 slices"
        `Quick
        test_js_match_result_exposes_numbered_captures_as_utf16_slices;
      Alcotest.test_case
        "JS match result exposes unicode capture as surrogate pair slice"
        `Quick
        test_js_match_result_exposes_unicode_capture_as_surrogate_pair_slice;
      Alcotest.test_case
        "JS match result exposes undefined capture"
        `Quick
        test_js_match_result_exposes_undefined_capture;
      Alcotest.test_case
        "JS match result exposes named captures"
        `Quick
        test_js_match_result_exposes_named_captures;
      Alcotest.test_case
        "JS match result exposes instance and iterator captures"
        `Quick
        test_js_match_result_exposes_instance_and_iterator_captures;
      Alcotest.test_case
        "JS string unicode lookbehind crosses surrogate pair"
        `Quick
        test_js_string_unicode_lookbehind_crosses_surrogate_pair;
      Alcotest.test_case "JS string character classes match raw UTF-16" `Quick
        test_js_string_character_classes_match_raw_utf16;
      Alcotest.test_case "JS string anchors use UTF-16 boundaries" `Quick
        test_js_string_anchors_use_utf16_boundaries;
      Alcotest.test_case
        "JS string unicode class escape consumes surrogate pair"
        `Quick
        test_js_string_unicode_class_escape_consumes_surrogate_pair;
      Alcotest.test_case
        "JS string unicode simple class consumes surrogate pair"
        `Quick
        test_js_string_unicode_simple_class_consumes_surrogate_pair;
      Alcotest.test_case "JS string ECMA whitespace class escapes" `Quick
        test_js_string_ecma_whitespace_class_escapes;
      Alcotest.test_case
        "JS string multiline anchors use ECMA line terminators"
        `Quick
        test_js_string_multiline_anchors_use_ecma_line_terminators;
      Alcotest.test_case
        "JS string word boundary uses Unicode WordCharacters"
        `Quick
        test_js_string_word_boundary_uses_unicode_wordcharacters;
      Alcotest.test_case "exec preserves leftmost alternative result" `Quick
        test_exec_preserves_leftmost_alternative_result;
      Alcotest.test_case "exec returns none without match" `Quick
        test_exec_returns_none_without_match;
      Alcotest.test_case "exec matches start anchor" `Quick
        test_exec_matches_start_anchor;
      Alcotest.test_case "search matches start anchor" `Quick
        test_search_matches_start_anchor;
      Alcotest.test_case "exec matches end anchor" `Quick
        test_exec_matches_end_anchor;
      Alcotest.test_case "search matches end anchor" `Quick
        test_search_matches_end_anchor;
      Alcotest.test_case "search matches dot atom" `Quick
        test_search_matches_dot_atom;
      Alcotest.test_case "search matches character class atoms" `Quick
        test_search_matches_character_class_atoms;
      Alcotest.test_case "search matches character class escapes" `Quick
        test_search_matches_character_class_escapes;
      Alcotest.test_case "compile accepts braced unicode escape with unicode flag"
        `Quick
        test_compile_accepts_braced_unicode_escape_with_unicode_flag;
      Alcotest.test_case "compile accepts legacy braced unicode text"
        `Quick
        test_compile_accepts_legacy_braced_unicode_text_without_unicode_flag;
      Alcotest.test_case "compile accepts legacy invalid braced unicode text"
        `Quick
        test_compile_accepts_legacy_invalid_braced_unicode_text;
      Alcotest.test_case
        "compile accepts duplicate named groups across disjunction"
        `Quick
        test_compile_accepts_duplicate_named_groups_across_disjunction;
      Alcotest.test_case
        "compile rejects duplicate named groups in same alternative"
        `Quick
        test_compile_rejects_duplicate_named_groups_in_same_alternative;
      Alcotest.test_case "compile rejects invalid named group start" `Quick
        test_compile_rejects_invalid_named_group_start;
      Alcotest.test_case
        "compile accepts named backreference with matching group"
        `Quick
        test_compile_accepts_named_backreference_with_matching_group;
      Alcotest.test_case
        "compile rejects named backreference without matching group"
        `Quick
        test_compile_rejects_named_backreference_without_matching_group;
    ]);
  ]
