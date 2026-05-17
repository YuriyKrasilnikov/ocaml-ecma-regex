type expected =
  | Match of
      { start_index : int
      ; end_index : int
      ; matched_units : int list
      }
  | No_match

type case =
  { name : string
  ; pattern : string
  ; flags : string
  ; input_units : int list
  ; expected : expected
  }

let flags_or_fail source =
  match Ecma_regex.flags_of_string source with
  | Ok flags -> flags
  | Error msg -> Alcotest.failf "invalid flags %S: %s" source msg
;;

let compile_or_fail ~flags source =
  match Ecma_regex.compile ~flags source with
  | Ok regexp -> regexp
  | Error msg -> Alcotest.failf "compile %S failed: %s" source msg
;;

let js_string_of_utf16_units_or_fail units =
  match Ecma_regex.js_string_of_utf16_code_units units with
  | Ok input -> input
  | Error msg -> Alcotest.failf "invalid UTF-16 input: %s" msg
;;

let match_ ?(start_index = 0) ?end_index matched_units =
  let end_index =
    match end_index with
    | Some index -> index
    | None -> start_index + List.length matched_units
  in
  Match { start_index; end_index; matched_units }
;;

let case ?(flags = "") name pattern input_units expected =
  { name; pattern; flags; input_units; expected }
;;

let check_match_result name ~start_index ~end_index ~matched_units actual =
  Alcotest.(check int) (name ^ ": start_index") start_index actual.Ecma_regex.js_start_index;
  Alcotest.(check int) (name ^ ": end_index") end_index actual.Ecma_regex.js_end_index;
  Alcotest.(check (list int))
    (name ^ ": matched UTF-16 units")
    matched_units
    (Ecma_regex.js_string_to_utf16_code_units actual.Ecma_regex.js_matched_text)
;;

let run_case { name; pattern; flags; input_units; expected } () =
  let flags = flags_or_fail flags in
  let regexp = compile_or_fail ~flags pattern in
  let input = js_string_of_utf16_units_or_fail input_units in
  match expected, Ecma_regex.exec_js regexp input with
  | No_match, None -> ()
  | No_match, Some actual ->
    Alcotest.failf
      "%s: unexpected match at UTF-16 %d..%d"
      name
      actual.Ecma_regex.js_start_index
      actual.Ecma_regex.js_end_index
  | Match _, None -> Alcotest.failf "%s: expected a match" name
  | Match { start_index; end_index; matched_units }, Some actual ->
    check_match_result name ~start_index ~end_index ~matched_units actual
;;

let digit_5 = [ 0x0035 ]
let letter_a = [ 0x0041 ]
let underscore = [ 0x005F ]
let long_s = [ 0x017F ]
let kelvin_sign = [ 0x212A ]
let nbsp = [ 0x00A0 ]
let line_separator = [ 0x2028 ]
let bom = [ 0xFEFF ]
let high_surrogate = [ 0xD83D ]
let grinning_face = [ 0xD83D; 0xDE00 ]
let adlam_alif = [ 0xD83A; 0xDD00 ]

let escape_cases =
  [ case "top \\d matches ASCII digit" "\\d" digit_5 (match_ digit_5)
  ; case ~flags:"u" "top \\d /u ignores non-digit surrogate pair" "\\d" grinning_face No_match
  ; case ~flags:"v" "top \\d /v ignores non-digit surrogate pair" "\\d" grinning_face No_match
  ; case "top \\D consumes one raw surrogate without Unicode semantics" "\\D" grinning_face (match_ high_surrogate)
  ; case ~flags:"u" "top \\D /u consumes a surrogate pair as one code point" "\\D" grinning_face (match_ grinning_face)
  ; case ~flags:"v" "top \\D /v consumes a surrogate pair as one code point" "\\D" grinning_face (match_ grinning_face)
  ; case ~flags:"u" "top \\D /u rejects ASCII digit" "\\D" digit_5 No_match
  ; case "top \\w matches ASCII underscore" "\\w" underscore (match_ underscore)
  ; case "top \\w without ignoreCase rejects long s" "\\w" long_s No_match
  ; case ~flags:"i" "top \\w /i without Unicode rejects long s" "\\w" long_s No_match
  ; case ~flags:"u" "top \\w /u without ignoreCase rejects long s" "\\w" long_s No_match
  ; case ~flags:"iu" "top \\w /iu accepts long s by simple folding" "\\w" long_s (match_ long_s)
  ; case ~flags:"v" "top \\w /v without ignoreCase rejects long s" "\\w" long_s No_match
  ; case ~flags:"iv" "top \\w /iv accepts long s by simple folding" "\\w" long_s (match_ long_s)
  ; case ~flags:"iu" "top \\w /iu accepts Kelvin sign by simple folding" "\\w" kelvin_sign (match_ kelvin_sign)
  ; case ~flags:"iv" "top \\w /iv accepts Kelvin sign by simple folding" "\\w" kelvin_sign (match_ kelvin_sign)
  ; case "top \\W without Unicode accepts long s as non-word" "\\W" long_s (match_ long_s)
  ; case ~flags:"iu" "top \\W /iu rejects long s" "\\W" long_s No_match
  ; case ~flags:"iv" "top \\W /iv rejects long s" "\\W" long_s No_match
  ; case "top \\s accepts no-break space" "\\s" nbsp (match_ nbsp)
  ; case "top \\S rejects no-break space" "\\S" nbsp No_match
  ; case "top \\s accepts ECMA line separator" "\\s" line_separator (match_ line_separator)
  ; case "top \\S rejects ECMA line separator" "\\S" line_separator No_match
  ; case ~flags:"v" "top \\s /v accepts byte order mark" "\\s" bom (match_ bom)
  ; case ~flags:"v" "top \\S /v rejects byte order mark" "\\S" bom No_match
  ; case "top \\S consumes one raw surrogate without Unicode semantics" "\\S" grinning_face (match_ high_surrogate)
  ; case ~flags:"u" "top \\S /u consumes surrogate pair as one non-space code point" "\\S" grinning_face (match_ grinning_face)
  ; case ~flags:"v" "top \\S /v consumes surrogate pair as one non-space code point" "\\S" grinning_face (match_ grinning_face)
  ]
;;

let character_class_cases =
  [ case "class [\\d] matches ASCII digit" "[\\d]" digit_5 (match_ digit_5)
  ; case "class [\\D] consumes one raw surrogate without Unicode semantics" "[\\D]" grinning_face (match_ high_surrogate)
  ; case ~flags:"u" "class [\\D] /u consumes a surrogate pair as one code point" "[\\D]" grinning_face (match_ grinning_face)
  ; case ~flags:"v" "class [\\D] /v consumes a surrogate pair as one code point" "[\\D]" grinning_face (match_ grinning_face)
  ; case ~flags:"u" "class [\\w] /u rejects long s without ignoreCase" "[\\w]" long_s No_match
  ; case ~flags:"iu" "class [\\w] /iu accepts long s by simple folding" "[\\w]" long_s (match_ long_s)
  ; case ~flags:"iv" "class [\\w] /iv accepts long s by simple folding" "[\\w]" long_s (match_ long_s)
  ; case ~flags:"iu" "class [\\W] /iu rejects long s" "[\\W]" long_s No_match
  ; case ~flags:"u" "class [\\W] /u accepts long s as non-word" "[\\W]" long_s (match_ long_s)
  ; case "class [\\s] accepts ECMA line separator" "[\\s]" line_separator (match_ line_separator)
  ; case "class [\\S] rejects ECMA line separator" "[\\S]" line_separator No_match
  ; case ~flags:"v" "class [\\s] /v accepts byte order mark" "[\\s]" bom (match_ bom)
  ; case ~flags:"v" "class [\\S] /v rejects byte order mark" "[\\S]" bom No_match
  ]
;;

let property_cases =
  [ case ~flags:"u" "property \\p{Emoji} /u consumes grinning face pair" "\\p{Emoji}" grinning_face (match_ grinning_face)
  ; case ~flags:"u" "property \\P{Emoji} /u rejects grinning face pair" "\\P{Emoji}" grinning_face No_match
  ; case ~flags:"v" "property \\p{Emoji} /v consumes grinning face pair" "\\p{Emoji}" grinning_face (match_ grinning_face)
  ; case ~flags:"v" "property \\P{Emoji} /v rejects grinning face pair" "\\P{Emoji}" grinning_face No_match
  ; case ~flags:"u" "property \\p{Script=Adlam} /u consumes Adlam pair" "\\p{Script=Adlam}" adlam_alif (match_ adlam_alif)
  ; case ~flags:"u" "property \\P{Script=Adlam} /u rejects Adlam pair" "\\P{Script=Adlam}" adlam_alif No_match
  ; case ~flags:"v" "property \\p{sc=Adlam} /v consumes Adlam pair" "\\p{sc=Adlam}" adlam_alif (match_ adlam_alif)
  ; case ~flags:"v" "property \\P{sc=Adlam} /v rejects Adlam pair" "\\P{sc=Adlam}" adlam_alif No_match
  ; case ~flags:"u" "property \\p{ASCII} /u accepts ASCII letter" "\\p{ASCII}" letter_a (match_ letter_a)
  ; case ~flags:"u" "property \\p{ASCII} /u rejects lone surrogate" "\\p{ASCII}" high_surrogate No_match
  ; case ~flags:"u" "property \\P{ASCII} /u accepts lone surrogate" "\\P{ASCII}" high_surrogate (match_ high_surrogate)
  ; case ~flags:"u" "class [\\p{Emoji}] /u consumes grinning face pair" "[\\p{Emoji}]" grinning_face (match_ grinning_face)
  ; case ~flags:"u" "class [\\P{Emoji}] /u rejects grinning face pair" "[\\P{Emoji}]" grinning_face No_match
  ; case ~flags:"u" "class [\\p{Script=Adlam}] /u consumes Adlam pair" "[\\p{Script=Adlam}]" adlam_alif (match_ adlam_alif)
  ; case ~flags:"u" "class [\\P{ASCII}] /u accepts lone surrogate" "[\\P{ASCII}]" high_surrogate (match_ high_surrogate)
  ; case ~flags:"u" "class [\\p{ASCII}] /u rejects lone surrogate" "[\\p{ASCII}]" high_surrogate No_match
  ]
;;

let boundary_cases =
  [ case "boundary \\b\\w matches ASCII word at start" "\\b\\w" letter_a (match_ letter_a)
  ; case "boundary \\B\\w rejects ASCII word at start" "\\B\\w" letter_a No_match
  ; case ~flags:"u" "boundary \\b_ /u sees long s then underscore as non-word to word" "\\b_" (long_s @ underscore) (match_ ~start_index:1 underscore)
  ; case ~flags:"u" "boundary \\B_ /u rejects long s then underscore" "\\B_" (long_s @ underscore) No_match
  ; case ~flags:"iu" "boundary \\B_ /iu sees long s then underscore as word to word" "\\B_" (long_s @ underscore) (match_ ~start_index:1 underscore)
  ; case ~flags:"iu" "boundary \\b_ /iu rejects long s then underscore" "\\b_" (long_s @ underscore) No_match
  ; case ~flags:"iv" "boundary \\B_ /iv sees long s then underscore as word to word" "\\B_" (long_s @ underscore) (match_ ~start_index:1 underscore)
  ; case "boundary \\B\\W accepts lone high surrogate as non-word" "\\B\\W" high_surrogate (match_ high_surrogate)
  ; case "boundary \\b\\W rejects lone high surrogate at start" "\\b\\W" high_surrogate No_match
  ; case ~flags:"u" "boundary \\B\\W /u accepts grinning face as one non-word code point" "\\B\\W" grinning_face (match_ grinning_face)
  ; case ~flags:"u" "boundary \\b\\W /u rejects grinning face at start" "\\b\\W" grinning_face No_match
  ]
;;

let tests =
  List.map
    (fun test_case -> Alcotest.test_case test_case.name `Quick (run_case test_case))
    (escape_cases @ character_class_cases @ property_cases @ boundary_cases)
;;

let () = Alcotest.run "raw-utf16-escape-matrix" [ "public exec_js matrix", tests ]
