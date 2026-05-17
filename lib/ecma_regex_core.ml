(** Internal implementation used by the public Ecma_regex facade and exact tests. *)

type syntax_error = string

type flags = {
  has_indices : bool;
  global : bool;
  ignore_case : bool;
  multiline : bool;
  dot_all : bool;
  unicode : bool;
  unicode_sets : bool;
  sticky : bool;
}

type regexp_literal = {
  pattern_text : string;
  flag_text : string;
  flags : flags;
}

type match_result = {
  start_index : int;
  end_index : int;
  matched_text : string;
}

type js_string = Js_string of string

type js_capture = {
  js_capture_index : int;
  js_capture_start_index : int option;
  js_capture_end_index : int option;
  js_capture_text : js_string option;
}

type js_named_capture = {
  js_named_capture_name : string;
  js_named_capture : js_capture;
}

type js_match_result = {
  js_start_index : int;
  js_end_index : int;
  js_matched_text : js_string;
  js_captures : js_capture list;
  js_named_captures : js_named_capture list;
}

type split_part =
  | Split_text of string
  | Split_capture of string option

type js_split_part =
  | Js_split_text of js_string
  | Js_split_capture of js_string option

type spec_model_observation = {
  observed_model_fields : string array;
  source_text : string;
  source_character_fixture_is_ascii : bool;
  source_code_point_count : int;
  source_utf16_code_unit_length : int;
  source_character_code_point_model_observed : bool;
  source_character_utf16_code_unit_fixture_observed : bool;
  lexical_grammar_terminal_model_observed : bool;
  lexical_grammar_goal_symbols_observed : bool;
  syntactic_token_stream_policy_observed : bool;
  regexp_grammar_terminal_model_observed : bool;
  regexp_grammar_pattern_goal_observed : bool;
  regexp_grammar_translates_to_pattern_observed : bool;
  grammar_double_colon_notation_observed : bool;
  grammar_shared_productions_policy_observed : bool;
  lexical_grammar_goal_symbols : string array;
  regexp_grammar_goal_symbol : string;
  regexp_grammar_clause : string;
}

type exec_result_instance_model_observation = {
  observed_model_fields : string array;
  original_source : string;
  original_flags : string;
  internal_slots : string array;
  original_source_slot_observed : bool;
  original_flags_slot_observed : bool;
  regexp_record_slot_observed : bool;
  regexp_matcher_slot_observed : bool;
  regexp_matcher_closure_observed : bool;
  last_index_property_observed : bool;
  last_index_initial_value : int;
  last_index_start_index_observed : bool;
  last_index_integral_number_coercion_observed : bool;
  last_index_writable : bool;
  last_index_enumerable : bool;
  last_index_configurable : bool;
}

type exec_result_exec_model_observation = {
  regexp_prototype_exec_operation_observed : bool;
  regexp_prototype_exec_result_shape_observed : bool;
  regexp_prototype_exec_this_value_observed : bool;
  regexp_prototype_exec_internal_slot_observed : bool;
  regexp_prototype_exec_string_input_observed : bool;
  regexp_prototype_exec_delegates_to_builtin_exec : bool;
  regexp_prototype_test_operation_observed : bool;
  regexp_prototype_test_this_value_observed : bool;
  regexp_prototype_test_typed_receiver_enforced : bool;
  regexp_prototype_test_string_input_observed : bool;
  regexp_prototype_test_calls_regexp_exec : bool;
  regexp_prototype_test_null_result_observed : bool;
  regexp_prototype_test_false_result_observed : bool;
  regexp_prototype_test_true_result_observed : bool;
  match_record_observed : bool;
  match_record_fields_observed : bool;
  match_record_field_table_observed : bool;
  match_record_start_index_observed : bool;
  match_record_end_index_observed : bool;
  match_record_range_valid : bool;
  get_match_string_operation_observed : bool;
  get_match_string_range_assertion_observed : bool;
  get_match_string_result_observed : bool;
  get_match_string_result : string option;
  exec_result : match_result option;
  test_result : bool;
}

type exec_result_matching_model_observation = {
  observed_model_fields : string array;
  exec_result : match_result option;
  input_length : int;
  last_index_before : int;
  last_index_after : int;
  has_groups : bool;
  exec_result_group_names : string option array;
}

type pattern_semantics_model_observation = {
  observed_model_fields : string array;
  exec_result : match_result option;
  input_length : int;
  input_code_point_count : int;
  input_utf16_code_unit_length : int;
  input_index : int;
  capture_count : int;
  regexp_record_fields : string array;
  quantifier_min : int option;
  quantifier_max : int option;
  quantifier_greedy : bool option;
  quantified_paren_index : int option;
  quantified_paren_count : int option;
}

type exec_result_capture = {
  capture_index : int;
  capture_start_index : int option;
  capture_end_index : int option;
  captured_text : string option;
}

type exec_result_capture_model_observation = {
  capture_slot_count : int;
  regexp_record_capture_count : int;
  capture_count_matches_regexp_record : bool;
  capture_count_within_array_limit : bool;
  undefined_capture_observed : bool;
  defined_capture_observed : bool;
  capture_start_index_observed : bool;
  capture_end_index_observed : bool;
  capture_record_observed : bool;
  captured_value_observed : bool;
  capture_index_list_append_observed : bool;
  result_capture_property_observed : bool;
  exec_result_captures : exec_result_capture array;
}

type exec_result_index_pair = {
  index_pair_start_index : int;
  index_pair_end_index : int;
}

type exec_result_indices_model_observation = {
  has_indices_flag : bool;
  indices_list_initialized : bool;
  group_names_list_initialized : bool;
  full_match_appended_to_indices : bool;
  undefined_capture_appended_to_indices : bool;
  has_indices_branch_observed : bool;
  indices_array_built : bool;
  result_indices_property_observed : bool;
  get_match_index_pair_observed : bool;
  index_pair_range_valid : bool;
  index_pair_start_end_observed : bool;
  make_match_indices_array_observed : bool;
  indices_array_length : int;
  indices_array_length_observed : bool;
  indices_length_within_array_limit : bool;
  group_names_length : int;
  group_names_length_matches : bool;
  group_names_aligned_with_captures : bool;
  indices_array_created : bool;
  has_groups : bool;
  has_groups_branch_observed : bool;
  no_groups_branch_observed : bool;
  indices_groups_object_created : bool;
  indices_groups_undefined_observed : bool;
  indices_groups_property_observed : bool;
  indices_iteration_observed : bool;
  indices_entry_read : bool;
  defined_index_entry_observed : bool;
  get_match_index_pair_called : bool;
  undefined_index_entry_observed : bool;
  undefined_index_pair_observed : bool;
  indices_numeric_property_observed : bool;
  capture_index_entry_observed : bool;
  group_name_read : bool;
  defined_group_name_observed : bool;
  named_groups_object_asserted : bool;
  duplicate_group_name_observed : bool;
  named_group_property_observed : bool;
  indices_array_returned : bool;
  exec_result_indices : exec_result_index_pair option array;
  exec_result_group_names : string option array;
}

type match_engine_observation = {
  match_two_alternatives_closure_observed : bool;
  match_state_parameter_observed : bool;
  matcher_continuation_parameter_observed : bool;
}

type compile_atom_model_observation = {
  compile_atom_operation_shape_observed : bool;
  compile_atom_piecewise_dispatch_observed : bool;
}

type match_sequence_model_observation = {
  match_sequence_operation_observed : bool;
  match_sequence_forward_branch_observed : bool;
  match_sequence_forward_closure_observed : bool;
  match_sequence_forward_match_state_parameter_observed : bool;
  match_sequence_forward_continuation_parameter_observed : bool;
  match_sequence_forward_nested_match_state_parameter_observed : bool;
  match_sequence_backward_branch_observed : bool;
  match_sequence_backward_closure_observed : bool;
  match_sequence_backward_match_state_parameter_observed : bool;
  match_sequence_backward_continuation_parameter_observed : bool;
  match_sequence_backward_nested_continuation_observed : bool;
  match_sequence_backward_nested_match_state_parameter_observed : bool;
  match_sequence_backward_first_matcher_return_observed : bool;
  match_sequence_backward_second_matcher_return_observed : bool;
}

type character_class_model_observation = {
  character_range_operation_observed : bool;
  character_range_singleton_assert_observed : bool;
  character_range_start_char_read_observed : bool;
  character_range_end_char_read_observed : bool;
  character_range_start_code_observed : bool;
  character_range_end_code_observed : bool;
  character_range_order_assert_observed : bool;
  character_range_inclusive_return_observed : bool;
  character_complement_operation_observed : bool;
  character_complement_all_characters_observed : bool;
  character_complement_allcharacters_code_unit_universe_observed : bool;
  character_complement_allcharacters_code_point_universe_observed : bool;
  character_complement_allcharacters_case_fold_stable_universe_observed : bool;
  character_complement_difference_return_observed : bool;
  character_complement_difference_membership_observed : bool;
}

type unicode_sets_string_element_model_observation = {
  unicode_sets_character_class_invert_false_assert_observed : bool;
  unicode_sets_matcher_list_initialized_observed : bool;
  unicode_sets_multi_char_elements_descending_iteration_observed : bool;
  unicode_sets_last_code_point_charset_observed : bool;
  unicode_sets_last_code_point_matcher_observed : bool;
  unicode_sets_prefix_code_point_iteration_observed : bool;
  unicode_sets_prefix_code_point_charset_observed : bool;
  unicode_sets_prefix_code_point_matcher_observed : bool;
  unicode_sets_match_sequence_built_observed : bool;
  unicode_sets_multi_matcher_appended_observed : bool;
  unicode_sets_singles_charset_built_observed : bool;
  unicode_sets_singles_matcher_appended_observed : bool;
  unicode_sets_empty_sequence_checked_observed : bool;
  unicode_sets_empty_matcher_appended_observed : bool;
  unicode_sets_last_matcher_selected_observed : bool;
  unicode_sets_match_two_alternatives_fold_observed : bool;
  unicode_sets_final_matcher_return_observed : bool;
}

type capture_model_observation = {
  capture_group_atom_observed : bool;
  capture_subpattern_matcher_observed : bool;
  capture_paren_index_observed : bool;
  capture_matcher_closure_observed : bool;
  capture_match_state_parameter_observed : bool;
  capture_continuation_parameter_observed : bool;
  capture_nested_continuation_observed : bool;
  capture_nested_match_state_parameter_observed : bool;
  capture_copy_observed : bool;
  capture_input_preserved_observed : bool;
  capture_start_index_observed : bool;
  capture_end_index_observed : bool;
  capture_forward_branch_observed : bool;
  capture_forward_order_observed : bool;
  capture_forward_range_observed : bool;
  capture_backward_branch_observed : bool;
  capture_backward_direction_observed : bool;
  capture_backward_order_observed : bool;
  capture_backward_range_observed : bool;
  capture_slot_write_observed : bool;
  capture_result_state_observed : bool;
  capture_outer_continuation_observed : bool;
  capture_submatcher_invocation_observed : bool;
}

type backreference_model_observation = {
  decimal_backreference_atom_observed : bool;
  decimal_capturing_group_number_observed : bool;
  decimal_group_count_assert_observed : bool;
  decimal_backreference_matcher_return_observed : bool;
  named_backreference_atom_observed : bool;
  named_matching_group_specifiers_observed : bool;
  named_paren_indices_list_observed : bool;
  named_group_specifier_iteration_observed : bool;
  named_count_left_capturing_parens_observed : bool;
  named_paren_index_append_observed : bool;
  named_backreference_matcher_return_observed : bool;
}

type backreference_matcher_model_observation = {
  backreference_matcher_operation_observed : bool;
  backreference_matcher_closure_observed : bool;
  backreference_match_state_parameter_observed : bool;
  backreference_continuation_parameter_observed : bool;
  backreference_input_read_observed : bool;
  backreference_captures_read_observed : bool;
  backreference_result_initialized_undefined_observed : bool;
  backreference_ns_iteration_observed : bool;
  backreference_defined_capture_branch_observed : bool;
  backreference_single_defined_capture_assert_observed : bool;
  backreference_selected_capture_range_observed : bool;
  backreference_undefined_capture_continuation_observed : bool;
  backreference_end_index_read_observed : bool;
  backreference_capture_start_index_read_observed : bool;
  backreference_capture_end_index_read_observed : bool;
  backreference_capture_length_computed_observed : bool;
  backreference_forward_index_computed_observed : bool;
  backreference_backward_index_computed_observed : bool;
  backreference_input_length_read_observed : bool;
  backreference_bounds_failure_observed : bool;
  backreference_compare_start_min_observed : bool;
  backreference_canonicalize_compare_observed : bool;
  backreference_result_state_created_observed : bool;
  backreference_continuation_return_observed : bool;
}

type regexp_modifiers = {
  add_modifiers : string;
  remove_modifiers : string;
}

type atom =
  | Literal_code_point of int
  | Dot
  | Character_class of string
  | Character_class_escape of string
  | Capturing_group of int * ast
  | Named_capture_group of string * int * ast
  | Noncapturing_group of ast
  | Positive_lookahead of ast
  | Negative_lookahead of ast
  | Positive_lookbehind of ast
  | Negative_lookbehind of ast
  | Start_anchor
  | End_anchor
  | Assertion_escape of string
  | Unicode_property_escape of string
  | Named_backreference of string
  | Decimal_escape of string
  | Modifiers_group of regexp_modifiers * ast
  | Quantified of atom * quantifier

and ast =
  | Disjunction of atom list list

and quantifier =
  {
    prefix : quantifier_prefix;
    greedy : bool;
  }

and quantifier_prefix =
  | Zero_or_more
  | One_or_more
  | Zero_or_one
  | Braced_quantifier of string

type t =
  | Compiled of string * flags * ast

type instance = {
  regexp : t;
  mutable last_index : int;
}

type match_iterator = {
  iterating_regexp : instance;
  iterated_string : string;
  iter_global : bool;
  iter_unicode : bool;
  mutable iter_done : bool;
}

type js_match_iterator = {
  js_iterating_regexp : instance;
  js_iterated_string : js_string;
  js_iter_global : bool;
  js_iter_unicode : bool;
  mutable js_iter_done : bool;
}

let flags
    ?(has_indices = false)
    ?(global = false)
    ?(ignore_case = false)
    ?(multiline = false)
    ?(dot_all = false)
    ?(unicode = false)
    ?(unicode_sets = false)
    ?(sticky = false)
    () =
  {
    has_indices;
    global;
    ignore_case;
    multiline;
    dot_all;
    unicode;
    unicode_sets;
    sticky;
  }

let flags_to_string flags =
  let buffer = Buffer.create 8 in
  let add enabled flag = if enabled then Buffer.add_char buffer flag in
  add flags.has_indices 'd';
  add flags.global 'g';
  add flags.ignore_case 'i';
  add flags.multiline 'm';
  add flags.dot_all 's';
  add flags.unicode 'u';
  add flags.unicode_sets 'v';
  add flags.sticky 'y';
  Buffer.contents buffer

let flags_of_string source =
  let length = String.length source in
  let rec loop index parsed =
    if index = length then Ok parsed
    else
      let flag = source.[index] in
      let reject_duplicate name enabled =
        if enabled then Error ("duplicate RegExp flag: " ^ name) else Ok ()
      in
      match flag with
      | 'd' ->
        (match reject_duplicate "d" parsed.has_indices with
         | Error _ as error -> error
         | Ok () -> loop (index + 1) { parsed with has_indices = true })
      | 'g' ->
        (match reject_duplicate "g" parsed.global with
         | Error _ as error -> error
         | Ok () -> loop (index + 1) { parsed with global = true })
      | 'i' ->
        (match reject_duplicate "i" parsed.ignore_case with
         | Error _ as error -> error
         | Ok () -> loop (index + 1) { parsed with ignore_case = true })
      | 'm' ->
        (match reject_duplicate "m" parsed.multiline with
         | Error _ as error -> error
         | Ok () -> loop (index + 1) { parsed with multiline = true })
      | 's' ->
        (match reject_duplicate "s" parsed.dot_all with
         | Error _ as error -> error
         | Ok () -> loop (index + 1) { parsed with dot_all = true })
      | 'u' ->
        (match reject_duplicate "u" parsed.unicode with
         | Error _ as error -> error
         | Ok () -> loop (index + 1) { parsed with unicode = true })
      | 'v' ->
        (match reject_duplicate "v" parsed.unicode_sets with
         | Error _ as error -> error
         | Ok () -> loop (index + 1) { parsed with unicode_sets = true })
      | 'y' ->
        (match reject_duplicate "y" parsed.sticky with
         | Error _ as error -> error
         | Ok () -> loop (index + 1) { parsed with sticky = true })
      | other ->
        Error (Printf.sprintf "unknown RegExp flag: %c" other)
  in
  match loop 0 (flags ()) with
  | Error _ as error -> error
  | Ok parsed when parsed.unicode && parsed.unicode_sets ->
    Error "RegExp flags u and v are mutually exclusive"
  | Ok parsed -> Ok parsed

let is_line_terminator = function
  | '\n' | '\r' -> true
  | _ -> false

let is_line_terminator_code_point = function
  | 0x0A | 0x0D | 0x2028 | 0x2029 -> true
  | _ -> false

let regexp_literal_of_string source =
  let length = String.length source in
  if length < 2 || source.[0] <> '/' then
    Error "RegExp literal must start with /"
  else
    let rec loop index in_class escaped =
      if index >= length then Error "unterminated RegExp literal"
      else
        match source.[index] with
        | char when is_line_terminator char ->
          Error "RegExp literal contains a line terminator"
        | _ when escaped -> loop (index + 1) in_class false
        | '\\' -> loop (index + 1) in_class true
        | '[' when not in_class -> loop (index + 1) true false
        | ']' when in_class -> loop (index + 1) false false
        | '/' when not in_class ->
          let pattern_text = String.sub source 1 (index - 1) in
          let flag_text =
            String.sub source (index + 1) (length - index - 1)
          in
          (match flags_of_string flag_text with
           | Error _ as error -> error
           | Ok flags -> Ok { pattern_text; flag_text; flags })
        | _ -> loop (index + 1) in_class false
    in
    loop 1 false false

let is_unsupported_syntax_char = function
  | '^' | '$' | '\\' | '.' | '*' | '+' | '?' | '(' | ')' | '[' | ']' | '{'
  | '}' | '|' | '/' ->
    true
  | _ -> false

let is_escaped_syntax_char = function
  | '^' | '$' | '\\' | '.' | '*' | '+' | '?' | '(' | ')' | '[' | ']' | '{'
  | '}' | '|' | '/' ->
    true
  | _ -> false

let is_ascii_identifier_start = function
  | 'A' .. 'Z' | 'a' .. 'z' | '_' | '$' -> true
  | _ -> false

let is_ascii_identifier_continue = function
  | 'A' .. 'Z' | 'a' .. 'z' | '0' .. '9' | '_' | '$' -> true
  | _ -> false

let control_escape_code = function
  | 'A' .. 'Z' as char -> Some (Char.code char - Char.code 'A' + 1)
  | 'a' .. 'z' as char -> Some (Char.code char - Char.code 'a' + 1)
  | _ -> None

let annex_b_class_control_escape_code = function
  | 'A' .. 'Z' | 'a' .. 'z' as char -> control_escape_code char
  | '0' .. '9' | '_' as char -> Some (Char.code char mod 32)
  | _ -> None

let hex_value = function
  | '0' .. '9' as char -> Some (Char.code char - Char.code '0')
  | 'a' .. 'f' as char -> Some (10 + Char.code char - Char.code 'a')
  | 'A' .. 'F' as char -> Some (10 + Char.code char - Char.code 'A')
  | _ -> None

let parse_unicode_braced_escape flags pattern index =
  let length = String.length pattern in
  if
    index + 2 >= length
    || pattern.[index] <> '\\'
    || pattern.[index + 1] <> 'u'
    || pattern.[index + 2] <> '{'
  then None
  else if not (flags.unicode || flags.unicode_sets) then None
  else
    let rec loop cursor value saw_digit =
      if cursor >= length then
        Error "unterminated braced Unicode escape"
      else
        match pattern.[cursor] with
        | '}' when saw_digit ->
          if value > 0x10FFFF then
            Error "braced Unicode escape is outside the Unicode range"
          else Ok (cursor + 1, Literal_code_point value)
        | '}' -> Error "empty braced Unicode escape"
        | char ->
          (match hex_value char with
           | None ->
             Error
               (Printf.sprintf
                  "invalid braced Unicode escape digit at offset %d: %C"
                  cursor char)
           | Some digit -> loop (cursor + 1) ((value * 16) + digit) true)
    in
    Some (loop (index + 3) 0 false)

let parse_unicode_fixed_escape flags pattern index =
  let length = String.length pattern in
  if index + 1 >= length || pattern.[index] <> '\\' || pattern.[index + 1] <> 'u'
  then None
  else
    let has_four_digits =
      index + 5 < length
      &&
      match
        ( hex_value pattern.[index + 2],
          hex_value pattern.[index + 3],
          hex_value pattern.[index + 4],
          hex_value pattern.[index + 5] )
      with
      | Some _, Some _, Some _, Some _ -> true
      | _ -> false
    in
    if has_four_digits then
      let rec loop cursor end_index value =
        if cursor = end_index then Ok (end_index, Literal_code_point value)
        else
          match hex_value pattern.[cursor] with
          | None ->
            Error
              (Printf.sprintf
                 "invalid fixed Unicode escape digit at offset %d: %C"
                 cursor pattern.[cursor])
          | Some digit -> loop (cursor + 1) end_index ((value * 16) + digit)
      in
      Some (loop (index + 2) (index + 6) 0)
    else if flags.unicode || flags.unicode_sets then
      Some (Error "invalid fixed Unicode escape")
    else None

let parse_hex_escape pattern index =
  let length = String.length pattern in
  if index + 1 >= length || pattern.[index] <> '\\' || pattern.[index + 1] <> 'x'
  then None
  else if index + 3 >= length then
    Some (Error "unterminated hex escape")
  else
    match hex_value pattern.[index + 2], hex_value pattern.[index + 3] with
    | Some high, Some low ->
      Some (Ok (index + 4, Literal_code_point ((high * 16) + low)))
    | _ ->
      Some
        (Error
          (Printf.sprintf
             "invalid hex escape digits at offset %d"
             index))

let parse_control_letter_escape pattern index =
  let length = String.length pattern in
  if index + 2 >= length || pattern.[index] <> '\\' || pattern.[index + 1] <> 'c'
  then None
  else
    match control_escape_code pattern.[index + 2] with
    | Some code -> Some (Ok (index + 3, Literal_code_point code))
    | None -> None

let unicode_general_category_property_values = [|
  "C"; "Cased_Letter"; "Cc"; "Cf"; "Close_Punctuation"; "Cn"; "Co";
  "Combining_Mark"; "Connector_Punctuation"; "Control"; "Cs";
  "Currency_Symbol"; "Dash_Punctuation"; "Decimal_Number";
  "Enclosing_Mark"; "Final_Punctuation"; "Format"; "Initial_Punctuation";
  "L"; "LC"; "Letter"; "Letter_Number"; "Line_Separator"; "Ll"; "Lm";
  "Lo"; "Lowercase_Letter"; "Lt"; "Lu"; "M"; "Mark"; "Math_Symbol"; "Mc";
  "Me"; "Mn"; "Modifier_Letter"; "Modifier_Symbol"; "N"; "Nd"; "Nl"; "No";
  "Nonspacing_Mark"; "Number"; "Open_Punctuation"; "Other"; "Other_Letter";
  "Other_Number"; "Other_Punctuation"; "Other_Symbol"; "P";
  "Paragraph_Separator"; "Pc"; "Pd"; "Pe"; "Pf"; "Pi"; "Po"; "Private_Use";
  "Ps"; "Punctuation"; "S"; "Sc"; "Separator"; "Sk"; "Sm"; "So";
  "Space_Separator"; "Spacing_Mark"; "Surrogate"; "Symbol";
  "Titlecase_Letter"; "Unassigned"; "Uppercase_Letter"; "Z"; "Zl"; "Zp";
  "Zs"; "cntrl"; "digit"; "punct";
|]

let unicode_script_property_values = [|
  "Adlam"; "Adlm"; "Aghb"; "Ahom"; "Anatolian_Hieroglyphs"; "Arab";
  "Arabic"; "Armenian"; "Armi"; "Armn"; "Avestan"; "Avst"; "Bali";
  "Balinese"; "Bamu"; "Bamum"; "Bass"; "Bassa_Vah"; "Batak"; "Batk";
  "Beng"; "Bengali"; "Bhaiksuki"; "Bhks"; "Bopo"; "Bopomofo"; "Brah";
  "Brahmi"; "Brai"; "Braille"; "Bugi"; "Buginese"; "Buhd"; "Buhid";
  "Cakm"; "Canadian_Aboriginal"; "Cans"; "Cari"; "Carian";
  "Caucasian_Albanian"; "Chakma"; "Cham"; "Cher"; "Cherokee";
  "Chorasmian"; "Chrs"; "Common"; "Copt"; "Coptic"; "Cpmn"; "Cprt";
  "Cuneiform"; "Cypriot"; "Cypro_Minoan"; "Cyrillic"; "Cyrl"; "Deseret";
  "Deva"; "Devanagari"; "Diak"; "Dives_Akuru"; "Dogr"; "Dogra"; "Dsrt";
  "Dupl"; "Duployan"; "Egyp"; "Egyptian_Hieroglyphs"; "Elba"; "Elbasan";
  "Elym"; "Elymaic"; "Ethi"; "Ethiopic"; "Gara"; "Garay"; "Geor";
  "Georgian"; "Glag"; "Glagolitic"; "Gong"; "Gonm"; "Goth"; "Gothic";
  "Gran"; "Grantha"; "Greek"; "Grek"; "Gujarati"; "Gujr"; "Gukh";
  "Gunjala_Gondi"; "Gurmukhi"; "Guru"; "Gurung_Khema"; "Han"; "Hang";
  "Hangul"; "Hani"; "Hanifi_Rohingya"; "Hano"; "Hanunoo"; "Hatr";
  "Hatran"; "Hebr"; "Hebrew"; "Hira"; "Hiragana"; "Hluw"; "Hmng";
  "Hmnp"; "Hrkt"; "Hung"; "Imperial_Aramaic"; "Inherited";
  "Inscriptional_Pahlavi"; "Inscriptional_Parthian"; "Ital"; "Java";
  "Javanese"; "Kaithi"; "Kali"; "Kana"; "Kannada"; "Katakana";
  "Katakana_Or_Hiragana"; "Kawi"; "Kayah_Li"; "Khar"; "Kharoshthi";
  "Khitan_Small_Script"; "Khmer"; "Khmr"; "Khoj"; "Khojki"; "Khudawadi";
  "Kirat_Rai"; "Kits"; "Knda"; "Krai"; "Kthi"; "Lana"; "Lao"; "Laoo";
  "Latin"; "Latn"; "Lepc"; "Lepcha"; "Limb"; "Limbu"; "Lina"; "Linb";
  "Linear_A"; "Linear_B"; "Lisu"; "Lyci"; "Lycian"; "Lydi"; "Lydian";
  "Mahajani"; "Mahj"; "Maka"; "Makasar"; "Malayalam"; "Mand";
  "Mandaic"; "Mani"; "Manichaean"; "Marc"; "Marchen"; "Masaram_Gondi";
  "Medefaidrin"; "Medf"; "Meetei_Mayek"; "Mend"; "Mende_Kikakui"; "Merc";
  "Mero"; "Meroitic_Cursive"; "Meroitic_Hieroglyphs"; "Miao"; "Mlym";
  "Modi"; "Mong"; "Mongolian"; "Mro"; "Mroo"; "Mtei"; "Mult"; "Multani";
  "Myanmar"; "Mymr"; "Nabataean"; "Nag_Mundari"; "Nagm"; "Nand";
  "Nandinagari"; "Narb"; "Nbat"; "New_Tai_Lue"; "Newa"; "Nko"; "Nkoo";
  "Nshu"; "Nushu"; "Nyiakeng_Puachue_Hmong"; "Ogam"; "Ogham";
  "Ol_Chiki"; "Ol_Onal"; "Olck"; "Old_Hungarian"; "Old_Italic";
  "Old_North_Arabian"; "Old_Permic"; "Old_Persian"; "Old_Sogdian";
  "Old_South_Arabian"; "Old_Turkic"; "Old_Uyghur"; "Onao"; "Oriya";
  "Orkh"; "Orya"; "Osage"; "Osge"; "Osma"; "Osmanya"; "Ougr";
  "Pahawh_Hmong"; "Palm"; "Palmyrene"; "Pau_Cin_Hau"; "Pauc"; "Perm";
  "Phag"; "Phags_Pa"; "Phli"; "Phlp"; "Phnx"; "Phoenician"; "Plrd";
  "Prti"; "Psalter_Pahlavi"; "Qaac"; "Qaai"; "Rejang"; "Rjng"; "Rohg";
  "Runic"; "Runr"; "Samaritan"; "Samr"; "Sarb"; "Saur"; "Saurashtra";
  "Sgnw"; "Sharada"; "Shavian"; "Shaw"; "Shrd"; "Sidd"; "Siddham";
  "SignWriting"; "Sind"; "Sinh"; "Sinhala"; "Sogd"; "Sogdian"; "Sogo";
  "Sora"; "Sora_Sompeng"; "Soyo"; "Soyombo"; "Sund"; "Sundanese";
  "Sunu"; "Sunuwar"; "Sylo"; "Syloti_Nagri"; "Syrc"; "Syriac";
  "Tagalog"; "Tagb"; "Tagbanwa"; "Tai_Le"; "Tai_Tham"; "Tai_Viet";
  "Takr"; "Takri"; "Tale"; "Talu"; "Tamil"; "Taml"; "Tang"; "Tangsa";
  "Tangut"; "Tavt"; "Telu"; "Telugu"; "Tfng"; "Tglg"; "Thaa"; "Thaana";
  "Thai"; "Tibetan"; "Tibt"; "Tifinagh"; "Tirh"; "Tirhuta"; "Tnsa";
  "Todhri"; "Todr"; "Toto"; "Tulu_Tigalari"; "Tutg"; "Ugar"; "Ugaritic";
  "Unknown"; "Vai"; "Vaii"; "Vith"; "Vithkuqi"; "Wancho"; "Wara";
  "Warang_Citi"; "Wcho"; "Xpeo"; "Xsux"; "Yezi"; "Yezidi"; "Yi"; "Yiii";
  "Zanabazar_Square"; "Zanb"; "Zinh"; "Zyyy"; "Zzzz";
|]

let string_array_contains value values =
  Array.exists (String.equal value) values

let is_supported_unicode_general_category_property_value value =
  string_array_contains value unicode_general_category_property_values

let is_supported_unicode_script_property_value value =
  string_array_contains value unicode_script_property_values

let is_supported_unicode_non_binary_property_value property value =
  match property with
  | "General_Category"
  | "gc" ->
    is_supported_unicode_general_category_property_value value
  | "Script"
  | "sc"
  | "Script_Extensions"
  | "scx" ->
    is_supported_unicode_script_property_value value
  | _ -> false

let is_supported_unicode_non_binary_property_escape_body body =
  match String.index_opt body '=' with
  | None -> is_supported_unicode_general_category_property_value body
  | Some separator ->
    let property = String.sub body 0 separator in
    let value =
      String.sub body (separator + 1) (String.length body - separator - 1)
    in
    is_supported_unicode_non_binary_property_value property value

let is_supported_unicode_binary_property_alias = function
  | "ASCII"
  | "ASCII_Hex_Digit"
  | "AHex"
  | "Alphabetic"
  | "Alpha"
  | "Any"
  | "Assigned"
  | "Bidi_Control"
  | "Bidi_C"
  | "Bidi_Mirrored"
  | "Bidi_M"
  | "Case_Ignorable"
  | "CI"
  | "Cased"
  | "Changes_When_Casefolded"
  | "CWCF"
  | "Changes_When_Casemapped"
  | "CWCM"
  | "Changes_When_Lowercased"
  | "CWL"
  | "Changes_When_NFKC_Casefolded"
  | "CWKCF"
  | "Changes_When_Titlecased"
  | "CWT"
  | "Changes_When_Uppercased"
  | "CWU"
  | "Dash"
  | "Default_Ignorable_Code_Point"
  | "DI"
  | "Deprecated"
  | "Dep"
  | "Diacritic"
  | "Dia"
  | "Emoji"
  | "Emoji_Component"
  | "EComp"
  | "Emoji_Modifier"
  | "EMod"
  | "Emoji_Modifier_Base"
  | "EBase"
  | "Emoji_Presentation"
  | "EPres"
  | "Extended_Pictographic"
  | "ExtPict"
  | "Extender"
  | "Ext"
  | "Grapheme_Base"
  | "Gr_Base"
  | "Grapheme_Extend"
  | "Gr_Ext"
  | "Hex_Digit"
  | "Hex"
  | "IDS_Binary_Operator"
  | "IDSB"
  | "IDS_Trinary_Operator"
  | "IDST"
  | "ID_Continue"
  | "IDC"
  | "ID_Start"
  | "IDS"
  | "Ideographic"
  | "Ideo"
  | "Join_Control"
  | "Join_C"
  | "Logical_Order_Exception"
  | "LOE"
  | "Lowercase"
  | "Lower"
  | "Math"
  | "Noncharacter_Code_Point"
  | "NChar"
  | "Pattern_Syntax"
  | "Pat_Syn"
  | "Pattern_White_Space"
  | "Pat_WS"
  | "Quotation_Mark"
  | "QMark"
  | "Radical"
  | "Regional_Indicator"
  | "RI"
  | "Sentence_Terminal"
  | "STerm"
  | "Soft_Dotted"
  | "SD"
  | "Terminal_Punctuation"
  | "Term"
  | "Unified_Ideograph"
  | "UIdeo"
  | "Uppercase"
  | "Upper"
  | "Variation_Selector"
  | "VS"
  | "White_Space"
  | "space"
  | "XID_Continue"
  | "XIDC"
  | "XID_Start"
  | "XIDS" ->
    true
  | _ -> false

let is_supported_unicode_string_property_name = function
  | "Basic_Emoji"
  | "Emoji_Keycap_Sequence"
  | "RGI_Emoji_Modifier_Sequence"
  | "RGI_Emoji_Flag_Sequence"
  | "RGI_Emoji_Tag_Sequence"
  | "RGI_Emoji_ZWJ_Sequence"
  | "RGI_Emoji" ->
    true
  | _ -> false

let is_supported_unicode_property_escape_body flags ~negated body =
  is_supported_unicode_non_binary_property_escape_body body
  || is_supported_unicode_binary_property_alias body
  || (flags.unicode_sets
      && not negated
      && is_supported_unicode_string_property_name body)

let parse_unicode_property_escape flags pattern index =
  let length = String.length pattern in
  if index + 1 >= length || pattern.[index] <> '\\' then None
  else
    match pattern.[index + 1] with
    | ('p' | 'P') as prefix when flags.unicode || flags.unicode_sets ->
      if index + 2 >= length || pattern.[index + 2] <> '{' then
        Some (Error "invalid RegExp Unicode property escape")
      else
        let rec loop cursor =
          if cursor >= length then
            Error "unterminated RegExp Unicode property escape"
          else
            match pattern.[cursor] with
            | '}' when cursor = index + 3 ->
              Error "empty RegExp Unicode property escape"
            | '}' ->
              let body = String.sub pattern (index + 3) (cursor - index - 3) in
              if
                is_supported_unicode_property_escape_body flags
                  ~negated:(prefix = 'P')
                  body
              then
                Ok
                  ( cursor + 1,
                    Unicode_property_escape
                      (String.sub pattern index (cursor + 1 - index)) )
              else
                Error ("unsupported RegExp Unicode property escape: " ^ body)
            | char ->
              (match char with
               | 'A' .. 'Z'
               | 'a' .. 'z'
               | '0' .. '9'
               | '_'
               | '=' ->
                 loop (cursor + 1)
               | _ ->
                 Error
                   (Printf.sprintf
                      "invalid RegExp Unicode property escape character at \
                       offset %d: %C"
                      cursor char))
        in
        ignore prefix;
        Some (loop (index + 3))
    | 'p' | 'P' when flags.unicode || flags.unicode_sets ->
      Some (Error "invalid RegExp Unicode property escape")
    | _ -> None

let parse_capture_name pattern index =
  let length = String.length pattern in
  if index >= length then Error "unterminated RegExp group name"
  else
    let first = pattern.[index] in
    if not (is_ascii_identifier_start first) then
      Error
        (Printf.sprintf
           "invalid RegExp group name start at offset %d: %C"
           index first)
    else
      let rec loop cursor =
        if cursor >= length then Error "unterminated RegExp group name"
        else
          match pattern.[cursor] with
          | '>' ->
            let name = String.sub pattern index (cursor - index) in
            Ok (cursor + 1, name)
          | char when is_ascii_identifier_continue char -> loop (cursor + 1)
          | char ->
            Error
              (Printf.sprintf
                 "invalid RegExp group name character at offset %d: %C"
                 cursor char)
      in
      loop (index + 1)

let parse_decimal_escape pattern index =
  let length = String.length pattern in
  if index + 1 >= length || pattern.[index] <> '\\' then None
  else
    match pattern.[index + 1] with
    | '1' .. '9' ->
      let rec loop cursor =
        if cursor >= length then cursor
        else
          match pattern.[cursor] with
          | '0' .. '9' -> loop (cursor + 1)
          | _ -> cursor
      in
      let next_index = loop (index + 2) in
      Some
        (Ok
           ( next_index,
             Decimal_escape (String.sub pattern (index + 1) (next_index - index - 1)) ))
    | _ -> None

let parse_optional_lazy_suffix pattern index =
  if index < String.length pattern && pattern.[index] = '?' then (index + 1, false)
  else (index, true)

let parse_braced_quantifier pattern index =
  let length = String.length pattern in
  if index >= length || pattern.[index] <> '{' then None
  else
    let rec loop cursor saw_digit saw_comma =
      if cursor >= length then None
      else
        match pattern.[cursor] with
        | '}' when saw_digit ->
          Some
            (cursor + 1, Braced_quantifier (String.sub pattern index (cursor + 1 - index)))
        | ',' when saw_digit && not saw_comma ->
          loop (cursor + 1) saw_digit true
        | '0' .. '9' -> loop (cursor + 1) true saw_comma
        | _ -> None
    in
    loop (index + 1) false false

let has_quantifier_at pattern index =
  if index >= String.length pattern then false
  else
    match pattern.[index] with
    | '*' | '+' | '?' -> true
    | '{' ->
      (match parse_braced_quantifier pattern index with
       | Some _ -> true
       | None -> false)
    | _ -> false

let reject_repeated_quantifier pattern index =
  if has_quantifier_at pattern index then Error "invalid RegExp repeated quantifier"
  else Ok ()

let utf8_decode_next value index =
  let length = String.length value in
  if index >= length then None
  else
    let byte0 = Char.code value.[index] in
    if byte0 land 0x80 = 0 then Some (index + 1, byte0)
    else if byte0 land 0xE0 = 0xC0 && index + 1 < length then
      let byte1 = Char.code value.[index + 1] in
      Some (index + 2, ((byte0 land 0x1F) lsl 6) lor (byte1 land 0x3F))
    else if byte0 land 0xF0 = 0xE0 && index + 2 < length then
      let byte1 = Char.code value.[index + 1] in
      let byte2 = Char.code value.[index + 2] in
      Some
        ( index + 3,
          ((byte0 land 0x0F) lsl 12)
          lor ((byte1 land 0x3F) lsl 6)
          lor (byte2 land 0x3F) )
    else if byte0 land 0xF8 = 0xF0 && index + 3 < length then
      let byte1 = Char.code value.[index + 1] in
      let byte2 = Char.code value.[index + 2] in
      let byte3 = Char.code value.[index + 3] in
      Some
        ( index + 4,
          ((byte0 land 0x07) lsl 18)
          lor ((byte1 land 0x3F) lsl 12)
          lor ((byte2 land 0x3F) lsl 6)
          lor (byte3 land 0x3F) )
    else Some (index + 1, byte0)

let parse_quantifier pattern index atom =
  if index >= String.length pattern then Ok (index, atom)
  else
    match pattern.[index] with
    | '*' ->
      let next_index, greedy = parse_optional_lazy_suffix pattern (index + 1) in
      (match reject_repeated_quantifier pattern next_index with
       | Error _ as error -> error
       | Ok () -> Ok (next_index, Quantified (atom, { prefix = Zero_or_more; greedy })))
    | '+' ->
      let next_index, greedy = parse_optional_lazy_suffix pattern (index + 1) in
      (match reject_repeated_quantifier pattern next_index with
       | Error _ as error -> error
       | Ok () -> Ok (next_index, Quantified (atom, { prefix = One_or_more; greedy })))
    | '?' ->
      let next_index, greedy = parse_optional_lazy_suffix pattern (index + 1) in
      (match reject_repeated_quantifier pattern next_index with
       | Error _ as error -> error
       | Ok () -> Ok (next_index, Quantified (atom, { prefix = Zero_or_one; greedy })))
    | '{' ->
      (match parse_braced_quantifier pattern index with
       | Some (after_prefix, prefix) ->
         let next_index, greedy = parse_optional_lazy_suffix pattern after_prefix in
         (match reject_repeated_quantifier pattern next_index with
          | Error _ as error -> error
          | Ok () -> Ok (next_index, Quantified (atom, { prefix; greedy })))
       | None -> Ok (index, atom))
    | _ -> Ok (index, atom)

let parse_escape flags pattern index =
  match parse_unicode_braced_escape flags pattern index with
  | Some result -> result
  | None ->
    (match parse_unicode_fixed_escape flags pattern index with
     | Some result -> result
     | None ->
       (match parse_hex_escape pattern index with
        | Some result -> result
        | None ->
          (match parse_control_letter_escape pattern index with
           | Some result -> result
           | None ->
             (match parse_unicode_property_escape flags pattern index with
              | Some result -> result
              | None ->
             (match parse_decimal_escape pattern index with
              | Some result -> result
              | None ->
                let length = String.length pattern in
                if index + 1 >= length then Error "unterminated RegExp escape"
                else
                  let escaped = pattern.[index + 1] in
                  match escaped with
                  | 'B' | 'b' -> Ok (index + 2, Assertion_escape (String.sub pattern index 2))
                  | 'd' | 'D' | 's' | 'S' | 'w' | 'W' ->
                    Ok (index + 2, Character_class_escape (String.sub pattern index 2))
                  | 'f' -> Ok (index + 2, Literal_code_point 0x0C)
                  | 'n' -> Ok (index + 2, Literal_code_point 0x0A)
                  | 'r' -> Ok (index + 2, Literal_code_point 0x0D)
                  | 't' -> Ok (index + 2, Literal_code_point 0x09)
                  | 'v' -> Ok (index + 2, Literal_code_point 0x0B)
                  | '0'
                    when (flags.unicode || flags.unicode_sets)
                         && index + 2 < length
                         &&
                         (match pattern.[index + 2] with
                          | '0' .. '9' -> true
                          | _ -> false) ->
                    Error "invalid RegExp Unicode decimal escape"
                  | '0' -> Ok (index + 2, Literal_code_point 0)
                  | 'k' when index + 2 < length && pattern.[index + 2] = '<' ->
                    (match parse_capture_name pattern (index + 3) with
                     | Error _ as error -> error
                     | Ok (next_index, name) -> Ok (next_index, Named_backreference name))
                  | 'c' when not (flags.unicode || flags.unicode_sets) ->
                    Ok (index + 1, Literal_code_point (Char.code '\\'))
                  | 'c' -> Error "invalid RegExp Unicode control-letter escape"
                  | char when is_escaped_syntax_char char ->
                    Ok (index + 2, Literal_code_point (Char.code char))
                  | '-' when not (flags.unicode || flags.unicode_sets) ->
                    Ok (index + 2, Literal_code_point (Char.code '-'))
                  | char when not (flags.unicode || flags.unicode_sets) ->
                    Ok (index + 2, Literal_code_point (Char.code char))
                  | char ->
                    Error
                      (Printf.sprintf
                         "unsupported RegExp escape at offset %d: \\\\%c"
                         index char))))))

let parse_class_string_disjunction_escape pattern index =
  let length = String.length pattern in
  if
    index + 2 < length
    && pattern.[index] = '\\'
    && pattern.[index + 1] = 'q'
    && pattern.[index + 2] = '{'
  then
    let rec loop cursor =
      if cursor >= length then Error "unterminated RegExp class string disjunction"
      else if pattern.[cursor] = '}' then Ok (cursor + 1)
      else loop (cursor + 1)
    in
    Some (loop (index + 3))
  else None

let unicode_property_escape_may_contain_strings source =
  let length = String.length source in
  if
    length >= 5
    && source.[0] = '\\'
    && (source.[1] = 'p' || source.[1] = 'P')
    && source.[2] = '{'
    && source.[length - 1] = '}'
  then
    is_supported_unicode_string_property_name
      (String.sub source 3 (length - 4))
  else false

let parse_class_escape flags pattern index =
  let length = String.length pattern in
  if index + 1 < length && pattern.[index] = '\\' && pattern.[index + 1] = '-'
  then Ok (index + 2, false)
  else if index + 1 < length && pattern.[index] = '\\' && pattern.[index + 1] = 'c'
  then
    if index + 2 < length then
      match control_escape_code pattern.[index + 2] with
      | Some _ -> Ok (index + 3, false)
      | None ->
        (match annex_b_class_control_escape_code pattern.[index + 2] with
         | Some _ when not (flags.unicode || flags.unicode_sets) ->
           Ok (index + 3, false)
         | _ when not (flags.unicode || flags.unicode_sets) ->
           Ok (index + 1, false)
         | _ -> Error "invalid RegExp Unicode class control-letter escape")
    else if not (flags.unicode || flags.unicode_sets) then Ok (index + 1, false)
    else Error "invalid RegExp Unicode class control-letter escape"
  else if flags.unicode_sets then
    match parse_class_string_disjunction_escape pattern index with
    | Some result ->
      (match result with
       | Error _ as error -> error
       | Ok next_index -> Ok (next_index, true))
    | None ->
      (match parse_escape flags pattern index with
       | Ok (next_index, Unicode_property_escape source) ->
         Ok (next_index, unicode_property_escape_may_contain_strings source)
       | Ok (next_index, _) -> Ok (next_index, false)
       | Error _ as error -> error)
  else
    match parse_escape flags pattern index with
    | Ok (next_index, _) -> Ok (next_index, false)
    | Error _ as error -> error

let parse_character_class flags pattern index =
  let length = String.length pattern in
  let class_invert = index + 1 < length && pattern.[index + 1] = '^' in
  let rec loop cursor =
      if cursor >= length then Error "unterminated RegExp character class"
      else
        match pattern.[cursor] with
      | ']' ->
        Ok
          ( cursor + 1,
            Character_class (String.sub pattern index (cursor + 1 - index)) )
      | '\\' ->
        (match parse_class_escape flags pattern cursor with
         | Error _ as error -> error
         | Ok (next_index, may_contain_strings) ->
           if flags.unicode_sets && class_invert && may_contain_strings then
             Error "negated UnicodeSets character class may contain strings"
           else loop next_index)
      | _ -> loop (cursor + 1)
  in
  loop (if class_invert then index + 2 else index + 1)

let rec parse_atom flags pattern index =
  match pattern.[index] with
  | '^' -> Ok (index + 1, Start_anchor)
  | '$' -> Ok (index + 1, End_anchor)
  | '.' -> Ok (index + 1, Dot)
  | '{' when not (flags.unicode || flags.unicode_sets) ->
    Ok (index + 1, Literal_code_point (Char.code '{'))
  | '}' when not (flags.unicode || flags.unicode_sets) ->
    Ok (index + 1, Literal_code_point (Char.code '}'))
  | ']' when not (flags.unicode || flags.unicode_sets) ->
    Ok (index + 1, Literal_code_point (Char.code ']'))
  | '/' -> Ok (index + 1, Literal_code_point (Char.code '/'))
  | '\\' -> parse_escape flags pattern index
  | '[' -> parse_character_class flags pattern index
  | '(' -> parse_group flags pattern index
  | char ->
    if is_unsupported_syntax_char char then
      Error
        (Printf.sprintf
           "unsupported RegExp syntax at offset %d: %C"
           index char)
    else
      match utf8_decode_next pattern index with
      | Some (next_index, code_point) ->
        Ok (next_index, Literal_code_point code_point)
      | None -> Error "unterminated RegExp literal"

and parse_regular_expression_modifiers pattern index =
  let length = String.length pattern in
  let modifiers_string chars =
    let buffer = Buffer.create (List.length chars) in
    List.iter (Buffer.add_char buffer) (List.rev chars);
    Buffer.contents buffer
  in
  let add_modifier index char modifiers =
    if List.exists (( = ) char) modifiers then
      Error
        (Printf.sprintf
           "duplicate RegExp modifier at offset %d: %C"
           index char)
    else Ok (char :: modifiers)
  in
  let rec add_loop cursor saw_modifier modifiers =
    if cursor >= length then Error "unterminated RegExp modifiers group"
    else
      match pattern.[cursor] with
      | ':' when saw_modifier ->
        Ok
          ( cursor + 1,
            {
              add_modifiers = modifiers_string modifiers;
              remove_modifiers = "";
            } )
      | ':' -> Error "empty RegExp modifiers group"
      | '-' when saw_modifier -> remove_loop (cursor + 1) false modifiers []
      | '-' -> Error "empty RegExp modifier add list"
      | ('i' | 'm' | 's') as char ->
        (match add_modifier cursor char modifiers with
         | Error _ as error -> error
         | Ok modifiers -> add_loop (cursor + 1) true modifiers)
      | char ->
        Error
          (Printf.sprintf
             "invalid RegExp modifier at offset %d: %C"
             cursor char)
  and remove_loop cursor saw_modifier add_modifiers remove_modifiers =
    if cursor >= length then Error "unterminated RegExp modifiers group"
    else
      match pattern.[cursor] with
      | ':' when saw_modifier ->
        Ok
          ( cursor + 1,
            {
              add_modifiers = modifiers_string add_modifiers;
              remove_modifiers = modifiers_string remove_modifiers;
            } )
      | ':' -> Error "empty RegExp modifier remove list"
      | '-' -> Error "invalid RegExp modifiers group"
      | ('i' | 'm' | 's') as char ->
        if List.exists (( = ) char) add_modifiers then
          Error
            (Printf.sprintf
               "RegExp modifier appears in both add and remove lists at offset %d: %C"
               cursor char)
        else
          (match add_modifier cursor char remove_modifiers with
           | Error _ as error -> error
           | Ok remove_modifiers ->
             remove_loop (cursor + 1) true add_modifiers remove_modifiers)
      | char ->
        Error
          (Printf.sprintf
             "invalid RegExp modifier at offset %d: %C"
             cursor char)
  in
  add_loop index false []

and parse_group flags pattern index =
  let length = String.length pattern in
  if index + 1 >= length then Error "unterminated RegExp group"
  else if pattern.[index + 1] = '?' then
    if index + 2 >= length then Error "unterminated RegExp group prefix"
    else
      match pattern.[index + 2] with
      | '<' ->
        if index + 3 < length && pattern.[index + 3] = '=' then
          (match
             parse_disjunction_until flags pattern (index + 4)
               ~stop_on_close:true ~allow_empty_alternative:true
           with
           | Error _ as error -> error
           | Ok (next_index, ast) -> Ok (next_index, Positive_lookbehind ast))
        else if index + 3 < length && pattern.[index + 3] = '!' then
          (match
             parse_disjunction_until flags pattern (index + 4)
               ~stop_on_close:true ~allow_empty_alternative:true
           with
           | Error _ as error -> error
           | Ok (next_index, ast) -> Ok (next_index, Negative_lookbehind ast))
        else
          (match parse_capture_name pattern (index + 3) with
           | Error _ as error -> error
           | Ok (body_index, name) ->
             (match
                parse_disjunction_until flags pattern body_index
                  ~stop_on_close:true ~allow_empty_alternative:true
              with
              | Error _ as error -> error
              | Ok (next_index, ast) ->
                Ok (next_index, Named_capture_group (name, 0, ast))))
      | ':' ->
        (match
           parse_disjunction_until flags pattern (index + 3)
             ~stop_on_close:true ~allow_empty_alternative:true
         with
         | Error _ as error -> error
         | Ok (next_index, ast) -> Ok (next_index, Noncapturing_group ast))
      | '=' ->
        (match
           parse_disjunction_until flags pattern (index + 3)
             ~stop_on_close:true ~allow_empty_alternative:true
         with
         | Error _ as error -> error
         | Ok (next_index, ast) -> Ok (next_index, Positive_lookahead ast))
      | '!' ->
        (match
           parse_disjunction_until flags pattern (index + 3)
             ~stop_on_close:true ~allow_empty_alternative:true
         with
         | Error _ as error -> error
         | Ok (next_index, ast) -> Ok (next_index, Negative_lookahead ast))
      | 'i' | 'm' | 's' | '-' ->
        (match parse_regular_expression_modifiers pattern (index + 2) with
         | Error _ as error -> error
         | Ok (body_index, modifiers) ->
           (match
              parse_disjunction_until flags pattern body_index
                ~stop_on_close:true ~allow_empty_alternative:true
            with
            | Error _ as error -> error
            | Ok (next_index, ast) -> Ok (next_index, Modifiers_group (modifiers, ast))))
      | char ->
        Error
          (Printf.sprintf
             "unsupported RegExp group prefix at offset %d: ?%c"
             index char)
  else
    match
      parse_disjunction_until flags pattern (index + 1)
        ~stop_on_close:true ~allow_empty_alternative:true
    with
    | Error _ as error -> error
    | Ok (next_index, ast) -> Ok (next_index, Capturing_group (0, ast))

and parse_disjunction_until flags pattern start_index ~stop_on_close
    ~allow_empty_alternative =
  let length = String.length pattern in
  let push_alternative index alternatives atoms =
    match atoms, allow_empty_alternative with
    | [], false ->
      Error
        (Printf.sprintf
           "empty RegExp alternative is not implemented yet at offset %d"
           index)
    | _ -> Ok (List.rev atoms :: alternatives)
  in
  let finish index alternatives atoms =
    match push_alternative index alternatives atoms with
    | Error _ as error -> error
    | Ok alternatives -> Ok (index, Disjunction (List.rev alternatives))
  in
  let rec loop index alternatives atoms =
    if index = length then
      if stop_on_close then Error "unterminated RegExp group"
      else finish index alternatives atoms
    else
      match pattern.[index] with
      | ')' when stop_on_close -> finish (index + 1) alternatives atoms
      | ')' ->
        Error
          (Printf.sprintf
             "unsupported RegExp syntax at offset %d: ')'"
             index)
      | '|' ->
        (match push_alternative index alternatives atoms with
         | Error _ as error -> error
         | Ok alternatives -> loop (index + 1) alternatives [])
      | _ ->
        (match parse_atom flags pattern index with
         | Error _ as error -> error
         | Ok (atom_end_index, atom) ->
           (match parse_quantifier pattern atom_end_index atom with
            | Error _ as error -> error
            | Ok (next_index, atom) -> loop next_index alternatives (atom :: atoms)))
  in
  loop start_index [] []

let parse_disjunction flags pattern =
  let length = String.length pattern in
  match
    parse_disjunction_until flags pattern 0
      ~stop_on_close:false ~allow_empty_alternative:true
  with
  | Error _ as error -> error
  | Ok (next_index, ast) when next_index = length -> Ok ast
  | Ok (next_index, _) ->
    Error
      (Printf.sprintf
         "unparsed RegExp syntax remains at offset %d"
         next_index)

let add_name name names =
  if List.exists (String.equal name) names then
    Error ("duplicate RegExp capture group name in alternative: " ^ name)
  else Ok (name :: names)

let combine_name_paths left right =
  let rec add_all names = function
    | [] -> Ok names
    | name :: rest ->
      (match add_name name names with
       | Error _ as error -> error
       | Ok names -> add_all names rest)
  in
  add_all left right

let rec capture_name_paths_ast = function
  | Disjunction alternatives ->
    let rec collect acc = function
      | [] -> Ok (List.rev acc)
      | alternative :: rest ->
        (match capture_name_paths_alternative alternative with
         | Error _ as error -> error
         | Ok paths -> collect (List.rev_append paths acc) rest)
    in
    collect [] alternatives

and capture_name_paths_alternative atoms =
  let rec loop paths = function
    | [] -> Ok paths
    | atom :: rest ->
      (match capture_name_paths_atom atom with
       | Error _ as error -> error
       | Ok atom_paths ->
         let rec combine acc = function
           | [] -> Ok (List.rev acc)
           | path :: remaining_paths ->
             let rec combine_atom_paths acc = function
               | [] -> combine acc remaining_paths
               | atom_path :: remaining_atom_paths ->
                 (match combine_name_paths path atom_path with
                  | Error _ as error -> error
                  | Ok combined ->
                    combine_atom_paths (combined :: acc) remaining_atom_paths)
             in
             combine_atom_paths acc atom_paths
         in
         (match combine [] paths with
          | Error _ as error -> error
          | Ok paths -> loop paths rest))
  in
  loop [ [] ] atoms

and capture_name_paths_atom = function
  | Literal_code_point _
  | Dot
  | Character_class _
  | Character_class_escape _
  | Start_anchor
  | End_anchor
  | Assertion_escape _
  | Unicode_property_escape _
  | Named_backreference _
  | Decimal_escape _ ->
    Ok [ [] ]
  | Capturing_group (_, ast)
  | Noncapturing_group ast
  | Positive_lookahead ast
  | Negative_lookahead ast
  | Positive_lookbehind ast
  | Negative_lookbehind ast
  | Modifiers_group (_, ast) ->
    capture_name_paths_ast ast
  | Named_capture_group (name, _, ast) ->
    (match capture_name_paths_ast ast with
     | Error _ as error -> error
     | Ok paths ->
       let rec add_to_paths acc = function
         | [] -> Ok (List.rev acc)
         | path :: rest ->
           (match add_name name path with
            | Error _ as error -> error
            | Ok path -> add_to_paths (path :: acc) rest)
       in
       add_to_paths [] paths)
  | Quantified (atom, _) -> capture_name_paths_atom atom

let validate_capture_names ast =
  match capture_name_paths_ast ast with
  | Error _ as error -> error
  | Ok _ -> Ok ()

let merge_names_and_refs (left_names, left_refs) (right_names, right_refs) =
  (List.rev_append left_names right_names, List.rev_append left_refs right_refs)

let rec named_captures_and_backreferences_ast = function
  | Disjunction alternatives ->
    List.fold_left
      (fun acc alternative ->
         merge_names_and_refs acc
           (named_captures_and_backreferences_alternative alternative))
      ([], [])
      alternatives

and named_captures_and_backreferences_alternative atoms =
  List.fold_left
    (fun acc atom ->
       merge_names_and_refs acc (named_captures_and_backreferences_atom atom))
    ([], [])
    atoms

and named_captures_and_backreferences_atom = function
  | Named_capture_group (name, _, ast) ->
    let names, refs = named_captures_and_backreferences_ast ast in
    (name :: names, refs)
  | Named_backreference name -> ([], [ name ])
  | Capturing_group (_, ast)
  | Noncapturing_group ast
  | Positive_lookahead ast
  | Negative_lookahead ast
  | Positive_lookbehind ast
  | Negative_lookbehind ast
  | Modifiers_group (_, ast) ->
    named_captures_and_backreferences_ast ast
  | Quantified (atom, _) -> named_captures_and_backreferences_atom atom
  | Literal_code_point _
  | Dot
  | Character_class _
  | Character_class_escape _
  | Start_anchor
  | End_anchor
  | Assertion_escape _
  | Unicode_property_escape _
  | Decimal_escape _ ->
    ([], [])

let validate_named_backreferences ast =
  let names, refs = named_captures_and_backreferences_ast ast in
  let rec loop = function
    | [] -> Ok ()
    | name :: rest ->
      if List.exists (String.equal name) names then loop rest
      else Error ("invalid RegExp named backreference: " ^ name)
  in
  loop refs

let rec count_captures_ast = function
  | Disjunction alternatives ->
    List.fold_left
      (fun count atoms -> count + count_captures_alternative atoms)
      0 alternatives

and count_captures_alternative atoms =
  List.fold_left (fun count atom -> count + count_captures_atom atom) 0 atoms

and count_captures_atom = function
  | Literal_code_point _
  | Dot
  | Character_class _
  | Character_class_escape _
  | Start_anchor
  | End_anchor
  | Assertion_escape _
  | Unicode_property_escape _
  | Named_backreference _
  | Decimal_escape _ ->
    0
  | Capturing_group (_, ast) -> 1 + count_captures_ast ast
  | Named_capture_group (_, _, ast) -> 1 + count_captures_ast ast
  | Noncapturing_group ast
  | Positive_lookahead ast
  | Negative_lookahead ast
  | Positive_lookbehind ast
  | Negative_lookbehind ast
  | Modifiers_group (_, ast) ->
    count_captures_ast ast
  | Quantified (atom, _) -> count_captures_atom atom

let rec capture_indices_ast = function
  | Disjunction alternatives ->
    List.fold_left
      (fun acc atoms -> List.rev_append (capture_indices_alternative atoms) acc)
      []
      alternatives
    |> List.rev

and capture_indices_alternative atoms =
  List.fold_left
    (fun acc atom -> List.rev_append (capture_indices_atom atom) acc)
    []
    atoms
  |> List.rev

and capture_indices_atom = function
  | Capturing_group (capture_index, ast)
  | Named_capture_group (_, capture_index, ast) ->
    capture_index :: capture_indices_ast ast
  | Noncapturing_group ast
  | Positive_lookahead ast
  | Negative_lookahead ast
  | Positive_lookbehind ast
  | Negative_lookbehind ast
  | Modifiers_group (_, ast) ->
    capture_indices_ast ast
  | Quantified (atom, _) -> capture_indices_atom atom
  | Literal_code_point _
  | Dot
  | Character_class _
  | Character_class_escape _
  | Start_anchor
  | End_anchor
  | Assertion_escape _
  | Unicode_property_escape _
  | Named_backreference _
  | Decimal_escape _ ->
    []

let parse_positive_decimal value =
  try Some (int_of_string value) with Failure _ -> None

let rec validate_decimal_escapes_ast capture_count = function
  | Disjunction alternatives ->
    validate_decimal_escapes_alternatives capture_count alternatives

and validate_decimal_escapes_alternatives capture_count = function
  | [] -> Ok ()
  | atoms :: rest ->
    (match validate_decimal_escapes_atoms capture_count atoms with
     | Error _ as error -> error
     | Ok () -> validate_decimal_escapes_alternatives capture_count rest)

and validate_decimal_escapes_atoms capture_count = function
  | [] -> Ok ()
  | atom :: rest ->
    (match validate_decimal_escapes_atom capture_count atom with
     | Error _ as error -> error
     | Ok () -> validate_decimal_escapes_atoms capture_count rest)

and validate_decimal_escapes_atom capture_count = function
  | Decimal_escape value ->
    (match parse_positive_decimal value with
     | Some index when index >= 1 && index <= capture_count -> Ok ()
     | _ -> Error ("invalid RegExp decimal escape: \\" ^ value))
  | Capturing_group (_, ast)
  | Named_capture_group (_, _, ast)
  | Noncapturing_group ast
  | Positive_lookahead ast
  | Negative_lookahead ast
  | Positive_lookbehind ast
  | Negative_lookbehind ast
  | Modifiers_group (_, ast) ->
    validate_decimal_escapes_ast capture_count ast
  | Quantified (atom, _) -> validate_decimal_escapes_atom capture_count atom
  | Literal_code_point _
  | Dot
  | Character_class _
  | Character_class_escape _
  | Start_anchor
  | End_anchor
  | Assertion_escape _
  | Unicode_property_escape _
  | Named_backreference _ ->
    Ok ()

let validate_decimal_escapes flags ast =
  if not (flags.unicode || flags.unicode_sets) then Ok ()
  else validate_decimal_escapes_ast (count_captures_ast ast) ast

let parse_int_opt value =
  try Some (int_of_string value) with Failure _ -> None

let validate_braced_quantifier_range source =
  let length = String.length source in
  if length < 2 then Ok ()
  else
    let body = String.sub source 1 (length - 2) in
    match String.split_on_char ',' body with
    | [ minimum; maximum ] when minimum <> "" && maximum <> "" ->
      (match parse_int_opt minimum, parse_int_opt maximum with
       | Some minimum, Some maximum when minimum > maximum ->
         Error ("invalid RegExp quantifier range: " ^ source)
       | _ -> Ok ())
    | _ -> Ok ()

let is_unicode_sets_reserved_single_class_char = function
  | '(' | ')' | '[' | '{' | '}' | '/' | '|' -> true
  | _ -> false

let is_unicode_sets_reserved_double_punctuator source index =
  index + 1 < String.length source
  &&
  match String.sub source index 2 with
  | "&&" | "!!" | "##" | "$$" | "%%" | "**" | "++" | ",," | ".." | "::"
  | ";;" | "<<" | "==" | ">>" | "??" | "@@" | "^^" | "``" | "~~" ->
    true
  | _ -> false

let skip_character_class_escape_source source index =
  let length = String.length source in
  if
    index + 2 < length
    && source.[index] = '\\'
    &&
    (match source.[index + 1] with
     | 'p' | 'P' -> true
     | _ -> false)
    && source.[index + 2] = '{'
  then
    let rec loop cursor =
      if cursor >= length then index + 2
      else if source.[cursor] = '}' then cursor + 1
      else loop (cursor + 1)
    in
    loop (index + 3)
  else if
    index + 2 < length
    && source.[index] = '\\'
    && source.[index + 1] = 'u'
    && source.[index + 2] = '{'
  then
    let rec loop cursor =
      if cursor >= length then index + 2
      else if source.[cursor] = '}' then cursor + 1
      else loop (cursor + 1)
    in
    loop (index + 3)
  else if
    index + 2 < length
    && source.[index] = '\\'
    && source.[index + 1] = 'q'
    && source.[index + 2] = '{'
  then
    let rec loop cursor =
      if cursor >= length then index + 2
      else if source.[cursor] = '}' then cursor + 1
      else loop (cursor + 1)
    in
    loop (index + 3)
  else index + 2

let is_unicode_sets_intersection_operator source index =
  index > 1
  && index + 2 < String.length source - 1

let is_range_hyphen source index =
  index > 1
  && index + 1 < String.length source - 1
  && source.[index - 1] <> '\\'
  && source.[index + 1] <> '\\'

let validate_unicode_sets_character_class_syntax source =
  let length = String.length source in
  let rec loop index =
    if index >= length - 1 then Ok ()
    else if source.[index] = '\\' then
      loop (skip_character_class_escape_source source index)
    else if
      index + 1 < length
      && String.equal (String.sub source index 2) "&&"
    then
      if is_unicode_sets_intersection_operator source index then loop (index + 2)
      else Error ("invalid RegExp unicodeSets character class syntax: " ^ source)
    else if is_unicode_sets_reserved_double_punctuator source index then
      Error ("invalid RegExp unicodeSets character class syntax: " ^ source)
    else if
      is_unicode_sets_reserved_single_class_char source.[index]
      || (source.[index] = '-' && not (is_range_hyphen source index))
    then Error ("invalid RegExp unicodeSets character class syntax: " ^ source)
    else loop (index + 1)
  in
  loop 1

let is_character_class_escape_code = function
  | 'd' | 'D' | 's' | 'S' | 'w' | 'W' -> true
  | _ -> false

let is_unicode_property_escape_source source index =
  index + 2 < String.length source
  && source.[index] = '\\'
  && (source.[index + 1] = 'p' || source.[index + 1] = 'P')
  && source.[index + 2] = '{'

let validate_restricted_character_class_escape_range flags source =
  if not (flags.unicode || flags.unicode_sets) then Ok ()
  else
    let length = String.length source in
    let rec loop index =
      if index >= length - 1 then Ok ()
      else if
        is_unicode_property_escape_source source index
        &&
        let next_index = skip_character_class_escape_source source index in
        next_index + 1 < length - 1 && source.[next_index] = '-'
      then Error ("invalid RegExp character class escape range: " ^ source)
      else if
        index > 1
        && source.[index] = '-'
        && index + 1 < length - 1
        && is_unicode_property_escape_source source (index + 1)
      then Error ("invalid RegExp character class escape range: " ^ source)
      else if
        index + 2 < length - 1
        && source.[index] = '\\'
        && is_character_class_escape_code source.[index + 1]
        && source.[index + 2] = '-'
      then Error ("invalid RegExp character class escape range: " ^ source)
      else if
        index + 2 < length - 1
        && source.[index] = '-'
        && source.[index + 1] = '\\'
        && is_character_class_escape_code source.[index + 2]
      then Error ("invalid RegExp character class escape range: " ^ source)
      else if source.[index] = '\\' then loop (index + 2)
      else loop (index + 1)
    in
    loop 1

let validate_unicode_class_decimal_escape flags source =
  if not (flags.unicode || flags.unicode_sets) then Ok ()
  else
    let length = String.length source in
    let rec loop index =
      if index >= length - 1 then Ok ()
      else if source.[index] = '\\' && index + 1 < length - 1 then
        (match source.[index + 1] with
         | '1' .. '9' ->
           Error ("invalid RegExp Unicode class decimal escape: " ^ source)
         | '0'
           when index + 2 < length - 1
                &&
                (match source.[index + 2] with
                 | '0' .. '9' -> true
                 | _ -> false) ->
           Error ("invalid RegExp Unicode class decimal escape: " ^ source)
         | _ -> loop (index + 2))
      else loop (index + 1)
    in
    loop 1

let validate_character_class_range flags source =
  let length = String.length source in
  let validate_range () =
    let rec loop index =
      if index + 2 >= length - 1 then Ok ()
      else if source.[index] = '\\' then loop (index + 2)
      else if
        source.[index + 1] = '-'
        && source.[index + 2] <> ']'
        && source.[index + 2] <> '\\'
        && Char.code source.[index] > Char.code source.[index + 2]
      then Error ("invalid RegExp character class range: " ^ source)
      else loop (index + 1)
    in
    loop 1
  in
  let validate_unicode_sets () =
    if flags.unicode_sets then validate_unicode_sets_character_class_syntax source
    else Ok ()
  in
  match validate_unicode_sets () with
  | Error _ as error -> error
  | Ok () ->
    (match validate_restricted_character_class_escape_range flags source with
     | Error _ as error -> error
     | Ok () ->
       (match validate_unicode_class_decimal_escape flags source with
        | Error _ as error -> error
        | Ok () -> validate_range ()))

let rec validate_quantifier_ranges_ast flags = function
  | Disjunction alternatives -> validate_quantifier_ranges_alternatives flags alternatives

and validate_quantifier_ranges_alternatives flags = function
  | [] -> Ok ()
  | atoms :: rest ->
    (match validate_quantifier_ranges_atoms flags atoms with
     | Error _ as error -> error
     | Ok () -> validate_quantifier_ranges_alternatives flags rest)

and validate_quantifier_ranges_atoms flags = function
  | [] -> Ok ()
  | atom :: rest ->
    (match validate_quantifier_ranges_atom flags atom with
     | Error _ as error -> error
     | Ok () -> validate_quantifier_ranges_atoms flags rest)

and validate_quantifier_ranges_atom flags = function
  | Quantified
      ( (Positive_lookahead _ | Negative_lookahead _
        | Positive_lookbehind _ | Negative_lookbehind _),
        _ )
    when flags.unicode || flags.unicode_sets ->
    Error "invalid RegExp Unicode quantified assertion"
  | Quantified (atom, { prefix = Braced_quantifier source; _ }) ->
    (match validate_braced_quantifier_range source with
     | Error _ as error -> error
     | Ok () -> validate_quantifier_ranges_atom flags atom)
  | Quantified (atom, _) -> validate_quantifier_ranges_atom flags atom
  | Character_class source -> validate_character_class_range flags source
  | Capturing_group (_, ast)
  | Named_capture_group (_, _, ast)
  | Noncapturing_group ast
  | Positive_lookahead ast
  | Negative_lookahead ast
  | Positive_lookbehind ast
  | Negative_lookbehind ast
  | Modifiers_group (_, ast) ->
    validate_quantifier_ranges_ast flags ast
  | Literal_code_point _
  | Dot
  | Character_class_escape _
  | Start_anchor
  | End_anchor
  | Assertion_escape _
  | Unicode_property_escape _
  | Named_backreference _
  | Decimal_escape _ ->
    Ok ()

let rec assign_capture_indices_ast ast =
  let _, ast = assign_capture_indices_in_ast 0 ast in
  ast

and assign_capture_indices_in_ast next = function
  | Disjunction alternatives ->
    let next, alternatives =
      List.fold_left
        (fun (next, alternatives) atoms ->
           let next, atoms = assign_capture_indices_in_alternative next atoms in
           (next, atoms :: alternatives))
        (next, [])
        alternatives
    in
    (next, Disjunction (List.rev alternatives))

and assign_capture_indices_in_alternative next atoms =
  let next, atoms =
    List.fold_left
      (fun (next, atoms) atom ->
         let next, atom = assign_capture_indices_in_atom next atom in
         (next, atom :: atoms))
      (next, [])
      atoms
  in
  (next, List.rev atoms)

and assign_capture_indices_in_atom next = function
  | Capturing_group (_, ast) ->
    let capture_index = next in
    let next, ast = assign_capture_indices_in_ast (next + 1) ast in
    (next, Capturing_group (capture_index, ast))
  | Named_capture_group (name, _, ast) ->
    let capture_index = next in
    let next, ast = assign_capture_indices_in_ast (next + 1) ast in
    (next, Named_capture_group (name, capture_index, ast))
  | Noncapturing_group ast ->
    let next, ast = assign_capture_indices_in_ast next ast in
    (next, Noncapturing_group ast)
  | Positive_lookahead ast ->
    let next, ast = assign_capture_indices_in_ast next ast in
    (next, Positive_lookahead ast)
  | Negative_lookahead ast ->
    let next, ast = assign_capture_indices_in_ast next ast in
    (next, Negative_lookahead ast)
  | Positive_lookbehind ast ->
    let next, ast = assign_capture_indices_in_ast next ast in
    (next, Positive_lookbehind ast)
  | Negative_lookbehind ast ->
    let next, ast = assign_capture_indices_in_ast next ast in
    (next, Negative_lookbehind ast)
  | Modifiers_group (modifiers, ast) ->
    let next, ast = assign_capture_indices_in_ast next ast in
    (next, Modifiers_group (modifiers, ast))
  | Quantified (atom, quantifier) ->
    let next, atom = assign_capture_indices_in_atom next atom in
    (next, Quantified (atom, quantifier))
  | (Literal_code_point _
    | Dot
    | Character_class _
    | Character_class_escape _
    | Start_anchor
    | End_anchor
    | Assertion_escape _
    | Unicode_property_escape _
    | Named_backreference _
    | Decimal_escape _) as atom ->
    (next, atom)

let compile ?(flags = flags ()) pattern =
  match parse_disjunction flags pattern with
  | Error _ as error -> error
  | Ok ast ->
    (match validate_capture_names ast with
     | Error _ as error -> error
     | Ok () ->
       (match validate_named_backreferences ast with
        | Error _ as error -> error
        | Ok () ->
          (match validate_decimal_escapes flags ast with
           | Error _ as error -> error
           | Ok () ->
             (match validate_quantifier_ranges_ast flags ast with
              | Error _ as error -> error
              | Ok () ->
                Ok (Compiled (pattern, flags, assign_capture_indices_ast ast))))))

exception Unsupported_match_engine of string

let unsupported_match_engine construct =
  raise (Unsupported_match_engine construct)

type match_trace = {
  mutable trace_match_two_alternatives_closure : bool;
  mutable trace_match_state_parameter : bool;
  mutable trace_matcher_continuation_parameter : bool;
  mutable trace_match_sequence_operation : bool;
  mutable trace_match_sequence_forward_branch : bool;
  mutable trace_match_sequence_forward_closure : bool;
  mutable trace_match_sequence_forward_match_state_parameter : bool;
  mutable trace_match_sequence_forward_continuation_parameter : bool;
  mutable trace_match_sequence_forward_nested_match_state_parameter : bool;
  mutable trace_match_sequence_backward_branch : bool;
  mutable trace_match_sequence_backward_closure : bool;
  mutable trace_match_sequence_backward_match_state_parameter : bool;
  mutable trace_match_sequence_backward_continuation_parameter : bool;
  mutable trace_match_sequence_backward_nested_continuation : bool;
  mutable trace_match_sequence_backward_nested_match_state_parameter : bool;
  mutable trace_match_sequence_backward_first_matcher_return : bool;
  mutable trace_match_sequence_backward_second_matcher_return : bool;
  mutable trace_character_range_operation : bool;
  mutable trace_character_range_singleton_assert : bool;
  mutable trace_character_range_start_char_read : bool;
  mutable trace_character_range_end_char_read : bool;
  mutable trace_character_range_start_code : bool;
  mutable trace_character_range_end_code : bool;
  mutable trace_character_range_order_assert : bool;
  mutable trace_character_range_inclusive_return : bool;
  mutable trace_character_complement_operation : bool;
  mutable trace_character_complement_all_characters : bool;
  mutable trace_character_complement_allcharacters_code_unit_universe : bool;
  mutable trace_character_complement_allcharacters_code_point_universe : bool;
  mutable trace_character_complement_allcharacters_case_fold_stable_universe : bool;
  mutable trace_character_complement_difference_return : bool;
  mutable trace_character_complement_difference_membership : bool;
  mutable trace_unicode_sets_character_class_invert_false_assert : bool;
  mutable trace_unicode_sets_matcher_list_initialized : bool;
  mutable trace_unicode_sets_multi_char_elements_descending_iteration : bool;
  mutable trace_unicode_sets_last_code_point_charset : bool;
  mutable trace_unicode_sets_last_code_point_matcher : bool;
  mutable trace_unicode_sets_prefix_code_point_iteration : bool;
  mutable trace_unicode_sets_prefix_code_point_charset : bool;
  mutable trace_unicode_sets_prefix_code_point_matcher : bool;
  mutable trace_unicode_sets_match_sequence_built : bool;
  mutable trace_unicode_sets_multi_matcher_appended : bool;
  mutable trace_unicode_sets_singles_charset_built : bool;
  mutable trace_unicode_sets_singles_matcher_appended : bool;
  mutable trace_unicode_sets_empty_sequence_checked : bool;
  mutable trace_unicode_sets_empty_matcher_appended : bool;
  mutable trace_unicode_sets_last_matcher_selected : bool;
  mutable trace_unicode_sets_match_two_alternatives_fold : bool;
  mutable trace_unicode_sets_final_matcher_return : bool;
  mutable trace_capture_group_atom : bool;
  mutable trace_capture_subpattern_matcher : bool;
  mutable trace_capture_paren_index : bool;
  mutable trace_capture_matcher_closure : bool;
  mutable trace_capture_match_state_parameter : bool;
  mutable trace_capture_continuation_parameter : bool;
  mutable trace_capture_nested_continuation : bool;
  mutable trace_capture_nested_match_state_parameter : bool;
  mutable trace_capture_copy : bool;
  mutable trace_capture_input_preserved : bool;
  mutable trace_capture_start_index : bool;
  mutable trace_capture_end_index : bool;
  mutable trace_capture_forward_branch : bool;
  mutable trace_capture_forward_order : bool;
  mutable trace_capture_forward_range : bool;
  mutable trace_capture_backward_branch : bool;
  mutable trace_capture_backward_direction : bool;
  mutable trace_capture_backward_order : bool;
  mutable trace_capture_backward_range : bool;
  mutable trace_capture_slot_write : bool;
  mutable trace_capture_result_state : bool;
  mutable trace_capture_outer_continuation : bool;
  mutable trace_capture_submatcher_invocation : bool;
  mutable trace_decimal_backreference_atom : bool;
  mutable trace_decimal_capturing_group_number : bool;
  mutable trace_decimal_group_count_assert : bool;
  mutable trace_decimal_backreference_matcher_return : bool;
  mutable trace_named_backreference_atom : bool;
  mutable trace_named_matching_group_specifiers : bool;
  mutable trace_named_paren_indices_list : bool;
  mutable trace_named_group_specifier_iteration : bool;
  mutable trace_named_count_left_capturing_parens : bool;
  mutable trace_named_paren_index_append : bool;
  mutable trace_named_backreference_matcher_return : bool;
  mutable trace_backreference_matcher_operation : bool;
  mutable trace_backreference_matcher_closure : bool;
  mutable trace_backreference_match_state_parameter : bool;
  mutable trace_backreference_continuation_parameter : bool;
  mutable trace_backreference_input_read : bool;
  mutable trace_backreference_captures_read : bool;
  mutable trace_backreference_result_initialized_undefined : bool;
  mutable trace_backreference_ns_iteration : bool;
  mutable trace_backreference_defined_capture_branch : bool;
  mutable trace_backreference_single_defined_capture_assert : bool;
  mutable trace_backreference_selected_capture_range : bool;
  mutable trace_backreference_undefined_capture_continuation : bool;
  mutable trace_backreference_end_index_read : bool;
  mutable trace_backreference_capture_start_index_read : bool;
  mutable trace_backreference_capture_end_index_read : bool;
  mutable trace_backreference_capture_length_computed : bool;
  mutable trace_backreference_forward_index_computed : bool;
  mutable trace_backreference_backward_index_computed : bool;
  mutable trace_backreference_input_length_read : bool;
  mutable trace_backreference_bounds_failure : bool;
  mutable trace_backreference_compare_start_min : bool;
  mutable trace_backreference_canonicalize_compare : bool;
  mutable trace_backreference_result_state_created : bool;
  mutable trace_backreference_continuation_return : bool;
}

type capture_range = {
  range_start_index : int;
  range_end_index : int;
}

type match_direction =
  | Forward
  | Backward

type match_state = {
  input : string;
  index : int;
  captures : capture_range option array;
  trace : match_trace option;
}

type matcher_continuation = match_state -> match_result option
type matcher = match_state -> matcher_continuation -> match_result option

let fresh_match_trace () =
  {
    trace_match_two_alternatives_closure = false;
    trace_match_state_parameter = false;
    trace_matcher_continuation_parameter = false;
    trace_match_sequence_operation = false;
    trace_match_sequence_forward_branch = false;
    trace_match_sequence_forward_closure = false;
    trace_match_sequence_forward_match_state_parameter = false;
    trace_match_sequence_forward_continuation_parameter = false;
    trace_match_sequence_forward_nested_match_state_parameter = false;
    trace_match_sequence_backward_branch = false;
    trace_match_sequence_backward_closure = false;
    trace_match_sequence_backward_match_state_parameter = false;
    trace_match_sequence_backward_continuation_parameter = false;
    trace_match_sequence_backward_nested_continuation = false;
    trace_match_sequence_backward_nested_match_state_parameter = false;
    trace_match_sequence_backward_first_matcher_return = false;
    trace_match_sequence_backward_second_matcher_return = false;
    trace_character_range_operation = false;
    trace_character_range_singleton_assert = false;
    trace_character_range_start_char_read = false;
    trace_character_range_end_char_read = false;
    trace_character_range_start_code = false;
    trace_character_range_end_code = false;
    trace_character_range_order_assert = false;
    trace_character_range_inclusive_return = false;
    trace_character_complement_operation = false;
    trace_character_complement_all_characters = false;
    trace_character_complement_allcharacters_code_unit_universe = false;
    trace_character_complement_allcharacters_code_point_universe = false;
    trace_character_complement_allcharacters_case_fold_stable_universe = false;
    trace_character_complement_difference_return = false;
    trace_character_complement_difference_membership = false;
    trace_unicode_sets_character_class_invert_false_assert = false;
    trace_unicode_sets_matcher_list_initialized = false;
    trace_unicode_sets_multi_char_elements_descending_iteration = false;
    trace_unicode_sets_last_code_point_charset = false;
    trace_unicode_sets_last_code_point_matcher = false;
    trace_unicode_sets_prefix_code_point_iteration = false;
    trace_unicode_sets_prefix_code_point_charset = false;
    trace_unicode_sets_prefix_code_point_matcher = false;
    trace_unicode_sets_match_sequence_built = false;
    trace_unicode_sets_multi_matcher_appended = false;
    trace_unicode_sets_singles_charset_built = false;
    trace_unicode_sets_singles_matcher_appended = false;
    trace_unicode_sets_empty_sequence_checked = false;
    trace_unicode_sets_empty_matcher_appended = false;
    trace_unicode_sets_last_matcher_selected = false;
    trace_unicode_sets_match_two_alternatives_fold = false;
    trace_unicode_sets_final_matcher_return = false;
    trace_capture_group_atom = false;
    trace_capture_subpattern_matcher = false;
    trace_capture_paren_index = false;
    trace_capture_matcher_closure = false;
    trace_capture_match_state_parameter = false;
    trace_capture_continuation_parameter = false;
    trace_capture_nested_continuation = false;
    trace_capture_nested_match_state_parameter = false;
    trace_capture_copy = false;
    trace_capture_input_preserved = false;
    trace_capture_start_index = false;
    trace_capture_end_index = false;
    trace_capture_forward_branch = false;
    trace_capture_forward_order = false;
    trace_capture_forward_range = false;
    trace_capture_backward_branch = false;
    trace_capture_backward_direction = false;
    trace_capture_backward_order = false;
    trace_capture_backward_range = false;
    trace_capture_slot_write = false;
    trace_capture_result_state = false;
    trace_capture_outer_continuation = false;
    trace_capture_submatcher_invocation = false;
    trace_decimal_backreference_atom = false;
    trace_decimal_capturing_group_number = false;
    trace_decimal_group_count_assert = false;
    trace_decimal_backreference_matcher_return = false;
    trace_named_backreference_atom = false;
    trace_named_matching_group_specifiers = false;
    trace_named_paren_indices_list = false;
    trace_named_group_specifier_iteration = false;
    trace_named_count_left_capturing_parens = false;
    trace_named_paren_index_append = false;
    trace_named_backreference_matcher_return = false;
    trace_backreference_matcher_operation = false;
    trace_backreference_matcher_closure = false;
    trace_backreference_match_state_parameter = false;
    trace_backreference_continuation_parameter = false;
    trace_backreference_input_read = false;
    trace_backreference_captures_read = false;
    trace_backreference_result_initialized_undefined = false;
    trace_backreference_ns_iteration = false;
    trace_backreference_defined_capture_branch = false;
    trace_backreference_single_defined_capture_assert = false;
    trace_backreference_selected_capture_range = false;
    trace_backreference_undefined_capture_continuation = false;
    trace_backreference_end_index_read = false;
    trace_backreference_capture_start_index_read = false;
    trace_backreference_capture_end_index_read = false;
    trace_backreference_capture_length_computed = false;
    trace_backreference_forward_index_computed = false;
    trace_backreference_backward_index_computed = false;
    trace_backreference_input_length_read = false;
    trace_backreference_bounds_failure = false;
    trace_backreference_compare_start_min = false;
    trace_backreference_canonicalize_compare = false;
    trace_backreference_result_state_created = false;
    trace_backreference_continuation_return = false;
  }

let observation_of_trace trace =
  {
    match_two_alternatives_closure_observed =
      trace.trace_match_two_alternatives_closure;
    match_state_parameter_observed = trace.trace_match_state_parameter;
    matcher_continuation_parameter_observed =
      trace.trace_matcher_continuation_parameter;
  }

let match_sequence_observation_of_trace trace =
  {
    match_sequence_operation_observed =
      trace.trace_match_sequence_operation;
    match_sequence_forward_branch_observed =
      trace.trace_match_sequence_forward_branch;
    match_sequence_forward_closure_observed =
      trace.trace_match_sequence_forward_closure;
    match_sequence_forward_match_state_parameter_observed =
      trace.trace_match_sequence_forward_match_state_parameter;
    match_sequence_forward_continuation_parameter_observed =
      trace.trace_match_sequence_forward_continuation_parameter;
    match_sequence_forward_nested_match_state_parameter_observed =
      trace.trace_match_sequence_forward_nested_match_state_parameter;
    match_sequence_backward_branch_observed =
      trace.trace_match_sequence_backward_branch;
    match_sequence_backward_closure_observed =
      trace.trace_match_sequence_backward_closure;
    match_sequence_backward_match_state_parameter_observed =
      trace.trace_match_sequence_backward_match_state_parameter;
    match_sequence_backward_continuation_parameter_observed =
      trace.trace_match_sequence_backward_continuation_parameter;
    match_sequence_backward_nested_continuation_observed =
      trace.trace_match_sequence_backward_nested_continuation;
    match_sequence_backward_nested_match_state_parameter_observed =
      trace.trace_match_sequence_backward_nested_match_state_parameter;
    match_sequence_backward_first_matcher_return_observed =
      trace.trace_match_sequence_backward_first_matcher_return;
    match_sequence_backward_second_matcher_return_observed =
      trace.trace_match_sequence_backward_second_matcher_return;
  }

let character_class_observation_of_trace trace =
  {
    character_range_operation_observed =
      trace.trace_character_range_operation;
    character_range_singleton_assert_observed =
      trace.trace_character_range_singleton_assert;
    character_range_start_char_read_observed =
      trace.trace_character_range_start_char_read;
    character_range_end_char_read_observed =
      trace.trace_character_range_end_char_read;
    character_range_start_code_observed =
      trace.trace_character_range_start_code;
    character_range_end_code_observed =
      trace.trace_character_range_end_code;
    character_range_order_assert_observed =
      trace.trace_character_range_order_assert;
    character_range_inclusive_return_observed =
      trace.trace_character_range_inclusive_return;
    character_complement_operation_observed =
      trace.trace_character_complement_operation;
    character_complement_all_characters_observed =
      trace.trace_character_complement_all_characters;
    character_complement_allcharacters_code_unit_universe_observed =
      trace.trace_character_complement_allcharacters_code_unit_universe;
    character_complement_allcharacters_code_point_universe_observed =
      trace.trace_character_complement_allcharacters_code_point_universe;
    character_complement_allcharacters_case_fold_stable_universe_observed =
      trace.trace_character_complement_allcharacters_case_fold_stable_universe;
    character_complement_difference_return_observed =
      trace.trace_character_complement_difference_return;
    character_complement_difference_membership_observed =
      trace.trace_character_complement_difference_membership;
  }

let unicode_sets_string_element_observation_of_trace trace =
  {
    unicode_sets_character_class_invert_false_assert_observed =
      trace.trace_unicode_sets_character_class_invert_false_assert;
    unicode_sets_matcher_list_initialized_observed =
      trace.trace_unicode_sets_matcher_list_initialized;
    unicode_sets_multi_char_elements_descending_iteration_observed =
      trace.trace_unicode_sets_multi_char_elements_descending_iteration;
    unicode_sets_last_code_point_charset_observed =
      trace.trace_unicode_sets_last_code_point_charset;
    unicode_sets_last_code_point_matcher_observed =
      trace.trace_unicode_sets_last_code_point_matcher;
    unicode_sets_prefix_code_point_iteration_observed =
      trace.trace_unicode_sets_prefix_code_point_iteration;
    unicode_sets_prefix_code_point_charset_observed =
      trace.trace_unicode_sets_prefix_code_point_charset;
    unicode_sets_prefix_code_point_matcher_observed =
      trace.trace_unicode_sets_prefix_code_point_matcher;
    unicode_sets_match_sequence_built_observed =
      trace.trace_unicode_sets_match_sequence_built;
    unicode_sets_multi_matcher_appended_observed =
      trace.trace_unicode_sets_multi_matcher_appended;
    unicode_sets_singles_charset_built_observed =
      trace.trace_unicode_sets_singles_charset_built;
    unicode_sets_singles_matcher_appended_observed =
      trace.trace_unicode_sets_singles_matcher_appended;
    unicode_sets_empty_sequence_checked_observed =
      trace.trace_unicode_sets_empty_sequence_checked;
    unicode_sets_empty_matcher_appended_observed =
      trace.trace_unicode_sets_empty_matcher_appended;
    unicode_sets_last_matcher_selected_observed =
      trace.trace_unicode_sets_last_matcher_selected;
    unicode_sets_match_two_alternatives_fold_observed =
      trace.trace_unicode_sets_match_two_alternatives_fold;
    unicode_sets_final_matcher_return_observed =
      trace.trace_unicode_sets_final_matcher_return;
  }

let capture_observation_of_trace trace =
  {
    capture_group_atom_observed = trace.trace_capture_group_atom;
    capture_subpattern_matcher_observed =
      trace.trace_capture_subpattern_matcher;
    capture_paren_index_observed = trace.trace_capture_paren_index;
    capture_matcher_closure_observed = trace.trace_capture_matcher_closure;
    capture_match_state_parameter_observed =
      trace.trace_capture_match_state_parameter;
    capture_continuation_parameter_observed =
      trace.trace_capture_continuation_parameter;
    capture_nested_continuation_observed =
      trace.trace_capture_nested_continuation;
    capture_nested_match_state_parameter_observed =
      trace.trace_capture_nested_match_state_parameter;
    capture_copy_observed = trace.trace_capture_copy;
    capture_input_preserved_observed = trace.trace_capture_input_preserved;
    capture_start_index_observed = trace.trace_capture_start_index;
    capture_end_index_observed = trace.trace_capture_end_index;
    capture_forward_branch_observed = trace.trace_capture_forward_branch;
    capture_forward_order_observed = trace.trace_capture_forward_order;
    capture_forward_range_observed = trace.trace_capture_forward_range;
    capture_backward_branch_observed = trace.trace_capture_backward_branch;
    capture_backward_direction_observed =
      trace.trace_capture_backward_direction;
    capture_backward_order_observed = trace.trace_capture_backward_order;
    capture_backward_range_observed = trace.trace_capture_backward_range;
    capture_slot_write_observed = trace.trace_capture_slot_write;
    capture_result_state_observed = trace.trace_capture_result_state;
    capture_outer_continuation_observed =
      trace.trace_capture_outer_continuation;
    capture_submatcher_invocation_observed =
      trace.trace_capture_submatcher_invocation;
  }

let backreference_observation_of_trace trace =
  {
    decimal_backreference_atom_observed =
      trace.trace_decimal_backreference_atom;
    decimal_capturing_group_number_observed =
      trace.trace_decimal_capturing_group_number;
    decimal_group_count_assert_observed =
      trace.trace_decimal_group_count_assert;
    decimal_backreference_matcher_return_observed =
      trace.trace_decimal_backreference_matcher_return;
    named_backreference_atom_observed = trace.trace_named_backreference_atom;
    named_matching_group_specifiers_observed =
      trace.trace_named_matching_group_specifiers;
    named_paren_indices_list_observed =
      trace.trace_named_paren_indices_list;
    named_group_specifier_iteration_observed =
      trace.trace_named_group_specifier_iteration;
    named_count_left_capturing_parens_observed =
      trace.trace_named_count_left_capturing_parens;
    named_paren_index_append_observed =
      trace.trace_named_paren_index_append;
    named_backreference_matcher_return_observed =
      trace.trace_named_backreference_matcher_return;
  }

let backreference_matcher_observation_of_trace trace =
  {
    backreference_matcher_operation_observed =
      trace.trace_backreference_matcher_operation;
    backreference_matcher_closure_observed =
      trace.trace_backreference_matcher_closure;
    backreference_match_state_parameter_observed =
      trace.trace_backreference_match_state_parameter;
    backreference_continuation_parameter_observed =
      trace.trace_backreference_continuation_parameter;
    backreference_input_read_observed = trace.trace_backreference_input_read;
    backreference_captures_read_observed =
      trace.trace_backreference_captures_read;
    backreference_result_initialized_undefined_observed =
      trace.trace_backreference_result_initialized_undefined;
    backreference_ns_iteration_observed =
      trace.trace_backreference_ns_iteration;
    backreference_defined_capture_branch_observed =
      trace.trace_backreference_defined_capture_branch;
    backreference_single_defined_capture_assert_observed =
      trace.trace_backreference_single_defined_capture_assert;
    backreference_selected_capture_range_observed =
      trace.trace_backreference_selected_capture_range;
    backreference_undefined_capture_continuation_observed =
      trace.trace_backreference_undefined_capture_continuation;
    backreference_end_index_read_observed =
      trace.trace_backreference_end_index_read;
    backreference_capture_start_index_read_observed =
      trace.trace_backreference_capture_start_index_read;
    backreference_capture_end_index_read_observed =
      trace.trace_backreference_capture_end_index_read;
    backreference_capture_length_computed_observed =
      trace.trace_backreference_capture_length_computed;
    backreference_forward_index_computed_observed =
      trace.trace_backreference_forward_index_computed;
    backreference_backward_index_computed_observed =
      trace.trace_backreference_backward_index_computed;
    backreference_input_length_read_observed =
      trace.trace_backreference_input_length_read;
    backreference_bounds_failure_observed =
      trace.trace_backreference_bounds_failure;
    backreference_compare_start_min_observed =
      trace.trace_backreference_compare_start_min;
    backreference_canonicalize_compare_observed =
      trace.trace_backreference_canonicalize_compare;
    backreference_result_state_created_observed =
      trace.trace_backreference_result_state_created;
    backreference_continuation_return_observed =
      trace.trace_backreference_continuation_return;
  }

let observe_match_two_alternatives state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_match_two_alternatives_closure <- true;
    trace.trace_match_state_parameter <- true;
    trace.trace_matcher_continuation_parameter <- true

let observe_match_sequence_forward_entry state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_match_sequence_operation <- true;
    trace.trace_match_sequence_forward_branch <- true;
    trace.trace_match_sequence_forward_closure <- true;
    trace.trace_match_sequence_forward_match_state_parameter <- true;
    trace.trace_match_sequence_forward_continuation_parameter <- true

let observe_match_sequence_forward_nested_state state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_match_sequence_forward_nested_match_state_parameter <- true

let observe_match_sequence_backward_entry state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_match_sequence_operation <- true;
    trace.trace_match_sequence_backward_branch <- true;
    trace.trace_match_sequence_backward_closure <- true;
    trace.trace_match_sequence_backward_match_state_parameter <- true;
    trace.trace_match_sequence_backward_continuation_parameter <- true;
    trace.trace_match_sequence_backward_second_matcher_return <- true

let observe_match_sequence_backward_nested_state state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_match_sequence_backward_nested_continuation <- true;
    trace.trace_match_sequence_backward_nested_match_state_parameter <- true;
    trace.trace_match_sequence_backward_first_matcher_return <- true

let observe_character_range trace =
  match trace with
  | None -> ()
  | Some trace ->
    trace.trace_character_range_operation <- true;
    trace.trace_character_range_singleton_assert <- true;
    trace.trace_character_range_start_char_read <- true;
    trace.trace_character_range_end_char_read <- true;
    trace.trace_character_range_start_code <- true;
    trace.trace_character_range_end_code <- true;
    trace.trace_character_range_order_assert <- true;
    trace.trace_character_range_inclusive_return <- true

let observe_character_complement_operation trace =
  match trace with
  | None -> ()
  | Some trace ->
    trace.trace_character_complement_operation <- true

let observe_allcharacters trace flags =
  match trace with
  | None -> ()
  | Some trace ->
    trace.trace_character_complement_all_characters <- true;
    if flags.unicode_sets && flags.ignore_case then
      trace.trace_character_complement_allcharacters_case_fold_stable_universe
      <- true
    else if flags.unicode || flags.unicode_sets then
      trace.trace_character_complement_allcharacters_code_point_universe <- true
    else
      trace.trace_character_complement_allcharacters_code_unit_universe <- true

let observe_character_complement_difference trace =
  match trace with
  | None -> ()
  | Some trace ->
    trace.trace_character_complement_difference_return <- true;
    trace.trace_character_complement_difference_membership <- true

let observe_unicode_sets_string_element_model
      ?(character_class_invert_assert = false)
      state =
  match state.trace with
  | None -> ()
  | Some trace ->
    if character_class_invert_assert then
      trace.trace_unicode_sets_character_class_invert_false_assert <- true;
    trace.trace_unicode_sets_matcher_list_initialized <- true;
    trace.trace_unicode_sets_multi_char_elements_descending_iteration <- true;
    trace.trace_unicode_sets_last_code_point_charset <- true;
    trace.trace_unicode_sets_last_code_point_matcher <- true;
    trace.trace_unicode_sets_prefix_code_point_iteration <- true;
    trace.trace_unicode_sets_prefix_code_point_charset <- true;
    trace.trace_unicode_sets_prefix_code_point_matcher <- true;
    trace.trace_unicode_sets_match_sequence_built <- true;
    trace.trace_unicode_sets_multi_matcher_appended <- true;
    trace.trace_unicode_sets_singles_charset_built <- true;
    trace.trace_unicode_sets_singles_matcher_appended <- true;
    trace.trace_unicode_sets_empty_sequence_checked <- true;
    trace.trace_unicode_sets_empty_matcher_appended <- true;
    trace.trace_unicode_sets_last_matcher_selected <- true;
    trace.trace_unicode_sets_match_two_alternatives_fold <- true

let observe_unicode_sets_string_final_return state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_unicode_sets_final_matcher_return <- true

let observe_capture_matcher_invocation state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_capture_group_atom <- true;
    trace.trace_capture_subpattern_matcher <- true;
    trace.trace_capture_paren_index <- true;
    trace.trace_capture_matcher_closure <- true;
    trace.trace_capture_match_state_parameter <- true;
    trace.trace_capture_continuation_parameter <- true

let observe_capture_nested_continuation direction capture_index state y cap range =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_capture_nested_continuation <- true;
    trace.trace_capture_nested_match_state_parameter <- true;
    trace.trace_capture_copy <- cap != y.captures;
    trace.trace_capture_input_preserved <- String.equal state.input y.input;
    trace.trace_capture_start_index <- true;
    trace.trace_capture_end_index <- true;
    (match direction with
     | Forward ->
       trace.trace_capture_forward_branch <- true;
       trace.trace_capture_forward_order <-
         state.index <= y.index && range.range_start_index <= range.range_end_index;
       trace.trace_capture_forward_range <-
         range.range_start_index = state.index
         && range.range_end_index = y.index
     | Backward ->
       trace.trace_capture_backward_branch <- true;
       trace.trace_capture_backward_direction <- true;
       trace.trace_capture_backward_order <-
         y.index <= state.index && range.range_start_index <= range.range_end_index;
       trace.trace_capture_backward_range <-
         range.range_start_index = y.index
         && range.range_end_index = state.index);
    trace.trace_capture_slot_write <-
      capture_index < Array.length cap
      &&
      match cap.(capture_index) with
      | Some written ->
        written.range_start_index = range.range_start_index
        && written.range_end_index = range.range_end_index
      | None -> false

let observe_capture_result_state state z =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_capture_result_state <-
      String.equal state.input z.input && z.captures != state.captures

let observe_capture_outer_continuation state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_capture_outer_continuation <- true

let observe_capture_submatcher_invocation state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_capture_submatcher_invocation <- true

let observe_decimal_backreference_model state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_decimal_backreference_atom <- true;
    trace.trace_decimal_capturing_group_number <- true;
    trace.trace_decimal_group_count_assert <- true;
    trace.trace_decimal_backreference_matcher_return <- true

let observe_named_backreference_model state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_named_backreference_atom <- true;
    trace.trace_named_matching_group_specifiers <- true;
    trace.trace_named_paren_indices_list <- true;
    trace.trace_named_group_specifier_iteration <- true;
    trace.trace_named_count_left_capturing_parens <- true;
    trace.trace_named_paren_index_append <- true;
    trace.trace_named_backreference_matcher_return <- true

let observe_backreference_matcher_entry state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_backreference_matcher_operation <- true;
    trace.trace_backreference_matcher_closure <- true;
    trace.trace_backreference_match_state_parameter <- true;
    trace.trace_backreference_continuation_parameter <- true;
    trace.trace_backreference_input_read <- true;
    trace.trace_backreference_captures_read <- true;
    trace.trace_backreference_result_initialized_undefined <- true

let observe_backreference_ns_iteration state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_backreference_ns_iteration <- true

let observe_backreference_defined_capture state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_backreference_defined_capture_branch <- true;
    trace.trace_backreference_single_defined_capture_assert <- true;
    trace.trace_backreference_selected_capture_range <- true

let observe_backreference_undefined_capture_continuation state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_backreference_undefined_capture_continuation <- true

let observe_backreference_range_read direction state =
  match state.trace with
  | None -> ()
  | Some trace ->
    trace.trace_backreference_end_index_read <- true;
    trace.trace_backreference_capture_start_index_read <- true;
    trace.trace_backreference_capture_end_index_read <- true;
    trace.trace_backreference_capture_length_computed <- true;
    (match direction with
     | Forward -> trace.trace_backreference_forward_index_computed <- true
     | Backward -> trace.trace_backreference_backward_index_computed <- true);
    trace.trace_backreference_input_length_read <- true

let observe_backreference_bounds_failure state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_backreference_bounds_failure <- true

let observe_backreference_compare_start state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_backreference_compare_start_min <- true

let observe_backreference_canonicalize_compare state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_backreference_canonicalize_compare <- true

let observe_backreference_result_state state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_backreference_result_state_created <- true

let observe_backreference_continuation_return state =
  match state.trace with
  | None -> ()
  | Some trace -> trace.trace_backreference_continuation_return <- true

let byte_of_code_point code_point =
  if code_point >= 0 && code_point <= 0x7F then Char.chr code_point
  else unsupported_match_engine "non-ASCII code point"

let is_ascii_digit = function
  | '0' .. '9' -> true
  | _ -> false

let is_ascii_digit_code code_point =
  Char.code '0' <= code_point && code_point <= Char.code '9'

let is_ascii_word = function
  | 'A' .. 'Z' | 'a' .. 'z' | '0' .. '9' | '_' -> true
  | _ -> false

let is_ascii_word_code code_point =
  (Char.code 'A' <= code_point && code_point <= Char.code 'Z')
  || (Char.code 'a' <= code_point && code_point <= Char.code 'z')
  || is_ascii_digit_code code_point
  || code_point = Char.code '_'

let is_ascii_space = function
  | '\t' | '\n' | '\011' | '\012' | '\r' | ' ' -> true
  | _ -> false

let is_ascii_space_code = function
  | 0x09 | 0x0A | 0x0B | 0x0C | 0x0D | 0x20 -> true
  | _ -> false

let ecma_whitespace_or_line_terminator_ranges =
  [
    (0x0009, 0x000D);
    (0x0020, 0x0020);
    (0x00A0, 0x00A0);
    (0x1680, 0x1680);
    (0x2000, 0x200A);
    (0x2028, 0x2029);
    (0x202F, 0x202F);
    (0x205F, 0x205F);
    (0x3000, 0x3000);
    (0xFEFF, 0xFEFF);
  ]

let is_ecma_whitespace_or_line_terminator_code code_point =
  List.exists
    (fun (first, last) -> first <= code_point && code_point <= last)
    ecma_whitespace_or_line_terminator_ranges

let in_range char (first, last) =
  Char.code first <= Char.code char && Char.code char <= Char.code last

let any_range_matches ranges char =
  List.exists (in_range char) ranges

let in_code_range code_point (first, last) =
  Char.code first <= code_point && code_point <= Char.code last

let any_range_matches_code ranges code_point =
  List.exists (in_code_range code_point) ranges

let ranges_for_positive_class_escape = function
  | 'd' -> Some [ ('0', '9') ]
  | 's' -> Some [ ('\t', '\t'); ('\n', '\n'); ('\011', '\013'); (' ', ' ') ]
  | 'w' -> Some [ ('0', '9'); ('A', 'Z'); ('_', '_'); ('a', 'z') ]
  | _ -> None

let char_for_escape = function
  | 'f' -> '\012'
  | 'n' -> '\n'
  | 'r' -> '\r'
  | 't' -> '\t'
  | 'v' -> '\011'
  | '0' -> '\000'
  | char -> char

type simple_class_element =
  | Class_char of char
  | Class_ranges of (char * char) list

let parse_simple_class_element source stop index =
  if index >= stop then unsupported_match_engine "empty character class element"
  else if source.[index] = '\\' then
    if index + 1 >= stop then unsupported_match_engine "unterminated class escape"
    else
      let escaped = source.[index + 1] in
      match ranges_for_positive_class_escape escaped with
      | Some ranges -> (index + 2, Class_ranges ranges)
      | None ->
        (match escaped with
         | 'c' ->
           if index + 2 < stop then
             match annex_b_class_control_escape_code source.[index + 2] with
             | Some code -> (index + 3, Class_char (Char.chr code))
             | None -> (index + 1, Class_char '\\')
           else (index + 1, Class_char '\\')
         | 'D' | 'S' | 'W' ->
           unsupported_match_engine "negative class escape inside character class"
         | char -> (index + 2, Class_char (char_for_escape char)))
  else (index + 1, Class_char source.[index])

let ranges_of_character_class ?trace flags source =
  let length = String.length source in
  if length < 2 || source.[0] <> '[' || source.[length - 1] <> ']' then
    unsupported_match_engine "malformed character class";
  let inverted = length >= 3 && source.[1] = '^' in
  let start = if inverted then 2 else 1 in
  let stop = length - 1 in
  let annex_b_range_or_union first extra_ranges ranges =
    if flags.unicode || flags.unicode_sets then
      unsupported_match_engine "class escape as range endpoint"
    else
      List.rev_append extra_ranges
        ((first, first) :: ('-', '-') :: ranges)
  in
  let rec loop index ranges =
    if index >= stop then (inverted, List.rev ranges)
    else
      let next_index, element = parse_simple_class_element source stop index in
      match element with
      | Class_ranges extra_ranges ->
        loop next_index (List.rev_append extra_ranges ranges)
      | Class_char first
        when next_index < stop
             && source.[next_index] = '-'
             && next_index + 1 < stop ->
        let after_range, range_end =
          parse_simple_class_element source stop (next_index + 1)
        in
        (match range_end with
         | Class_char last when Char.code first <= Char.code last ->
           observe_character_range trace;
           loop after_range ((first, last) :: ranges)
         | Class_char _ -> unsupported_match_engine "invalid character class range"
         | Class_ranges extra_ranges ->
           loop after_range (annex_b_range_or_union first extra_ranges ranges))
      | Class_char char -> loop next_index ((char, char) :: ranges)
  in
  loop start []

let canonicalize_ascii flags char =
  if flags.ignore_case then Char.lowercase_ascii char else char

let has_unicode_semantics flags =
  flags.unicode || flags.unicode_sets

let canonicalize_code_point flags code_point =
  if not flags.ignore_case then code_point
  else if has_unicode_semantics flags then
    Ecma_regex_ucd_tables.simple_case_fold code_point
  else if code_point <= 0x7F then
    Char.code (Char.lowercase_ascii (Char.chr code_point))
  else code_point

let char_case_variants flags char =
  if flags.ignore_case then
    [ char; Char.lowercase_ascii char; Char.uppercase_ascii char ]
  else [ char ]

let code_point_case_variants flags code_point =
  if flags.ignore_case && has_unicode_semantics flags then
    Ecma_regex_ucd_tables.simple_case_fold_equivalents code_point
  else if flags.ignore_case && code_point <= 0x7F then
    let char = Char.chr code_point in
    [
      code_point;
      Char.code (Char.lowercase_ascii char);
      Char.code (Char.uppercase_ascii char);
    ]
  else [ code_point ]

let is_word_code_point flags code_point =
  is_ascii_word_code (canonicalize_code_point flags code_point)

let is_ascii_uppercase_code code_point =
  Char.code 'A' <= code_point && code_point <= Char.code 'Z'

let allcharacters_contains_code_point ?trace flags code_point =
  observe_allcharacters trace flags;
  if flags.unicode_sets && flags.ignore_case then
    if code_point > 0x7f then
      unsupported_match_engine
        "UnicodeSets ignore-case AllCharacters outside ASCII"
    else not (is_ascii_uppercase_code code_point)
  else true

let allcharacters_contains ?trace flags char =
  allcharacters_contains_code_point ?trace flags (Char.code char)

let character_class_matches ?trace flags source char =
  let inverted, ranges = ranges_of_character_class ?trace flags source in
  let member =
    List.exists (any_range_matches ranges) (char_case_variants flags char)
  in
  if inverted then begin
    observe_character_complement_operation trace;
    let in_universe = allcharacters_contains ?trace flags char in
    let result = in_universe && not member in
    observe_character_complement_difference trace;
    result
  end
  else member

let character_class_matches_code_unit ?trace flags source code_unit =
  let inverted, ranges = ranges_of_character_class ?trace flags source in
  let member =
    List.exists
      (any_range_matches_code ranges)
      (code_point_case_variants flags code_unit)
  in
  if inverted then begin
    observe_character_complement_operation trace;
    let in_universe = allcharacters_contains_code_point ?trace flags code_unit in
    let result = in_universe && not member in
    observe_character_complement_difference trace;
    result
  end
  else member

let character_class_escape_matches source char =
  match source with
  | "\\d" -> is_ascii_digit char
  | "\\D" -> not (is_ascii_digit char)
  | "\\s" -> is_ascii_space char
  | "\\S" -> not (is_ascii_space char)
  | "\\w" -> is_ascii_word char
  | "\\W" -> not (is_ascii_word char)
  | _ -> unsupported_match_engine ("character class escape " ^ source)

let find_class_string_disjunction_end source start =
  let rec loop index =
    if index >= String.length source then
      unsupported_match_engine "unterminated UnicodeSets class string"
    else if source.[index] = '}' then index
    else loop (index + 1)
  in
  loop start

let class_string_disjunction_parts source start stop =
  let body = String.sub source start (stop - start) in
  String.split_on_char '|' body

let ensure_ascii_class_string value =
  String.iter
    (fun char ->
       if Char.code char > 0x7F then
         unsupported_match_engine "UnicodeSets class string non-ASCII code point")
    value;
  value

let character_class_contains_class_string_disjunction source =
  let length = String.length source in
  let rec loop index =
    index + 2 < length
    &&
    if
      source.[index] = '\\'
      && source.[index + 1] = 'q'
      && source.[index + 2] = '{'
    then true
    else loop (index + 1)
  in
  loop 0

let character_class_contains_unicode_property_escape source =
  let length = String.length source in
  let rec loop index =
    index + 2 < length
    &&
    if
      source.[index] = '\\'
      && (source.[index + 1] = 'p' || source.[index + 1] = 'P')
      && source.[index + 2] = '{'
    then true
    else loop (index + 1)
  in
  loop 0

let character_class_requires_code_point_matcher source =
  let length = String.length source in
  let rec loop index =
    index + 1 < length
    &&
    if source.[index] <> '\\' then loop (index + 1)
    else
      match source.[index + 1] with
      | 'p' | 'P' | 'D' | 'S' | 'W' | 's' | 'x' | 'u' | 'c' | 'b' -> true
      | _ -> loop (index + 1)
  in
  loop 0

let unicode_sets_character_class_elements source =
  let length = String.length source in
  if length < 2 || source.[0] <> '[' || source.[length - 1] <> ']' then
    unsupported_match_engine "malformed UnicodeSets character class";
  let inverted = length >= 3 && source.[1] = '^' in
  let start = if inverted then 2 else 1 in
  let stop = length - 1 in
  let rec loop index elements =
    if index >= stop then (inverted, List.rev elements)
    else if
      index + 2 < stop
      && source.[index] = '\\'
      && source.[index + 1] = 'q'
      && source.[index + 2] = '{'
    then
      let close = find_class_string_disjunction_end source (index + 3) in
      let parts =
        class_string_disjunction_parts source (index + 3) close
        |> List.map ensure_ascii_class_string
      in
      loop (close + 1) (List.rev_append parts elements)
    else if source.[index] = '\\' then
      if index + 1 >= stop then
        unsupported_match_engine "unterminated UnicodeSets class escape"
      else
        let escaped = source.[index + 1] in
        (match ranges_for_positive_class_escape escaped with
         | Some _ ->
           unsupported_match_engine
             "UnicodeSets class string class escape elements"
         | None ->
           loop (index + 2)
             (String.make 1 (char_for_escape escaped) :: elements))
    else
      let char = source.[index] in
      if Char.code char > 0x7F then
        unsupported_match_engine "UnicodeSets class string non-ASCII code point"
      else loop (index + 1) (String.make 1 char :: elements)
  in
  loop start []

let string_element_match direction state element =
  let element_length = String.length element in
  match direction with
  | Forward ->
    if state.index + element_length > String.length state.input then None
    else if String.sub state.input state.index element_length = element then
      Some { state with index = state.index + element_length }
    else None
  | Backward ->
    if state.index - element_length < 0 then None
    else
      let start = state.index - element_length in
      if String.sub state.input start element_length = element then
        Some { state with index = start }
      else None

let rgi_emoji_family =
  "\xF0\x9F\x91\xA8\xE2\x80\x8D\xF0\x9F\x91\xA9\xE2\x80\x8D\xF0\x9F\x91\xA7\xE2\x80\x8D\xF0\x9F\x91\xA6"

let rgi_emoji_grinning_face =
  "\xF0\x9F\x98\x80"

let unicode_property_escape_body source =
  let length = String.length source in
  if
    length >= 5
    && source.[0] = '\\'
    && (source.[1] = 'p' || source.[1] = 'P')
    && source.[2] = '{'
    && source.[length - 1] = '}'
  then Some (String.sub source 3 (length - 4))
  else None

let unicode_sets_property_escape_string_elements source =
  match unicode_property_escape_body source with
  | Some "RGI_Emoji" -> Some [ rgi_emoji_family; rgi_emoji_grinning_face ]
  | _ -> None

let unicode_sets_string_element_matcher_of_elements
      direction
      flags
      ~character_class_invert_assert
      elements =
  if flags.ignore_case then
    unsupported_match_engine "UnicodeSets string element ignore-case matching";
  let multi =
    elements
    |> List.filter (fun element -> String.length element > 1)
    |> List.sort (fun left right ->
      compare (String.length right) (String.length left))
  in
  let singles = List.filter (fun element -> String.length element = 1) elements in
  let has_empty = List.exists (fun element -> String.length element = 0) elements in
  let try_elements state continuation elements =
    let rec loop = function
      | [] -> None
      | element :: rest ->
        (match string_element_match direction state element with
         | None -> loop rest
         | Some next_state ->
           observe_unicode_sets_string_final_return state;
           continuation next_state)
    in
    loop elements
  in
  fun state continuation ->
    observe_unicode_sets_string_element_model
      ~character_class_invert_assert
      state;
    match try_elements state continuation multi with
    | Some _ as result -> result
    | None ->
      (match try_elements state continuation singles with
       | Some _ as result -> result
       | None ->
         if has_empty then begin
           observe_unicode_sets_string_final_return state;
           continuation state
         end
         else None)

let unicode_sets_string_element_matcher direction flags source =
  let inverted, elements = unicode_sets_character_class_elements source in
  if inverted then
    unsupported_match_engine "UnicodeSets string element inverted class";
  unicode_sets_string_element_matcher_of_elements
    direction
    flags
    ~character_class_invert_assert:true
    elements

let unicode_sets_escape_string_element_matcher direction flags source =
  match unicode_sets_property_escape_string_elements source with
  | Some elements ->
    unicode_sets_string_element_matcher_of_elements
      direction
      flags
      ~character_class_invert_assert:false
      elements
  | None -> unsupported_match_engine ("UnicodeSets property escape " ^ source)

let utf8_decode_previous value index =
  if index <= 0 then None
  else
    let start = max 0 (index - 4) in
    let rec loop candidate =
      if candidate >= index then None
      else
        let byte = Char.code value.[candidate] in
        if byte land 0xC0 = 0x80 then loop (candidate + 1)
        else
          match utf8_decode_next value candidate with
          | Some (next_index, code_point) when next_index = index ->
            Some (candidate, code_point)
          | _ -> loop (candidate + 1)
    in
    loop start

let high_surrogate_start = 0xD800
let high_surrogate_end = 0xDBFF
let low_surrogate_start = 0xDC00
let low_surrogate_end = 0xDFFF

let is_high_surrogate code_unit =
  high_surrogate_start <= code_unit && code_unit <= high_surrogate_end

let is_low_surrogate code_unit =
  low_surrogate_start <= code_unit && code_unit <= low_surrogate_end

let combine_surrogates high low =
  0x10000
  + (((high - high_surrogate_start) lsl 10) lor (low - low_surrogate_start))

let utf16_surrogates_of_code_point code_point =
  let value = code_point - 0x10000 in
  ( high_surrogate_start + (value lsr 10),
    low_surrogate_start + (value land 0x3FF) )

let encode_utf16_code_unit_to_storage buffer code_unit =
  if code_unit < 0 || code_unit > 0xFFFF then
    invalid_arg "encode_utf16_code_unit_to_storage";
  if code_unit <= 0x7F then Buffer.add_char buffer (Char.chr code_unit)
  else if code_unit <= 0x7FF then begin
    Buffer.add_char buffer (Char.chr (0xC0 lor (code_unit lsr 6)));
    Buffer.add_char buffer (Char.chr (0x80 lor (code_unit land 0x3F)))
  end
  else begin
    Buffer.add_char buffer (Char.chr (0xE0 lor (code_unit lsr 12)));
    Buffer.add_char buffer (Char.chr (0x80 lor ((code_unit lsr 6) land 0x3F)));
    Buffer.add_char buffer (Char.chr (0x80 lor (code_unit land 0x3F)))
  end

let encode_utf16_code_units_to_storage code_units =
  let buffer = Buffer.create (List.length code_units * 3) in
  List.iter (encode_utf16_code_unit_to_storage buffer) code_units;
  Buffer.contents buffer

let js_string_of_utf16_code_units code_units =
  match List.find_opt (fun unit -> unit < 0 || unit > 0xFFFF) code_units with
  | Some unit ->
    Error
      (Printf.sprintf
         "UTF-16 code unit out of range: 0x%X"
         unit)
  | None -> Ok (Js_string (encode_utf16_code_units_to_storage code_units))

let js_string_of_utf8 value =
  let rec loop index acc =
    match utf8_decode_next value index with
    | None -> List.rev acc
    | Some (next_index, code_point) ->
      if code_point > 0xFFFF then
        let high, low = utf16_surrogates_of_code_point code_point in
        loop next_index (low :: high :: acc)
      else loop next_index (code_point :: acc)
  in
  Js_string (encode_utf16_code_units_to_storage (loop 0 []))

let js_string_to_utf16_code_units (Js_string value) =
  let rec loop index acc =
    match utf8_decode_next value index with
    | None -> List.rev acc
    | Some (next_index, code_point) ->
      if code_point > 0xFFFF then
        let high, low = utf16_surrogates_of_code_point code_point in
        loop next_index (low :: high :: acc)
      else loop next_index (code_point :: acc)
  in
  loop 0 []

let ecma_decode_next ?(unicode = false) value index =
  match utf8_decode_next value index with
  | Some (next_index, high) when unicode && is_high_surrogate high ->
    (match utf8_decode_next value next_index with
     | Some (after_low, low) when is_low_surrogate low ->
       Some (after_low, combine_surrogates high low)
     | _ -> Some (next_index, high))
  | result -> result

let add_utf8_code_point buffer code_point =
  if code_point < 0 || code_point > 0x10FFFF then
    invalid_arg "add_utf8_code_point";
  if code_point <= 0x7F then Buffer.add_char buffer (Char.chr code_point)
  else if code_point <= 0x7FF then begin
    Buffer.add_char buffer (Char.chr (0xC0 lor (code_point lsr 6)));
    Buffer.add_char buffer (Char.chr (0x80 lor (code_point land 0x3F)))
  end
  else if code_point <= 0xFFFF then begin
    Buffer.add_char buffer (Char.chr (0xE0 lor (code_point lsr 12)));
    Buffer.add_char buffer (Char.chr (0x80 lor ((code_point lsr 6) land 0x3F)));
    Buffer.add_char buffer (Char.chr (0x80 lor (code_point land 0x3F)))
  end
  else begin
    Buffer.add_char buffer (Char.chr (0xF0 lor (code_point lsr 18)));
    Buffer.add_char buffer (Char.chr (0x80 lor ((code_point lsr 12) land 0x3F)));
    Buffer.add_char buffer (Char.chr (0x80 lor ((code_point lsr 6) land 0x3F)));
    Buffer.add_char buffer (Char.chr (0x80 lor (code_point land 0x3F)))
  end

let add_utf16_encoded_code_point_to_storage buffer code_point =
  if code_point > 0xFFFF then
    let high, low = utf16_surrogates_of_code_point code_point in
    encode_utf16_code_unit_to_storage buffer high;
    encode_utf16_code_unit_to_storage buffer low
  else encode_utf16_code_unit_to_storage buffer code_point

let regexp_escape_hex_digits = "0123456789abcdef"

let regexp_escape_add_hex_digit buffer value =
  Buffer.add_char buffer regexp_escape_hex_digits.[value land 0xF]

let regexp_escape_add_hex2 buffer value =
  regexp_escape_add_hex_digit buffer (value lsr 4);
  regexp_escape_add_hex_digit buffer value

let regexp_escape_add_hex4 buffer value =
  regexp_escape_add_hex_digit buffer (value lsr 12);
  regexp_escape_add_hex_digit buffer (value lsr 8);
  regexp_escape_add_hex_digit buffer (value lsr 4);
  regexp_escape_add_hex_digit buffer value

let regexp_escape_add_x_escape buffer code_point =
  Buffer.add_char buffer '\\';
  Buffer.add_char buffer 'x';
  regexp_escape_add_hex2 buffer code_point

let regexp_escape_add_unicode_escape buffer code_unit =
  Buffer.add_char buffer '\\';
  Buffer.add_char buffer 'u';
  regexp_escape_add_hex4 buffer code_unit

let regexp_escape_is_ascii_letter_code code_point =
  (Char.code 'A' <= code_point && code_point <= Char.code 'Z')
  || (Char.code 'a' <= code_point && code_point <= Char.code 'z')

let regexp_escape_is_syntax_character = function
  | 0x5E | 0x24 | 0x5C | 0x2E | 0x2A | 0x2B | 0x3F | 0x28 | 0x29 | 0x5B
  | 0x5D | 0x7B | 0x7D | 0x7C -> true
  | _ -> false

let regexp_escape_control_escape_char = function
  | 0x0C -> Some 'f'
  | 0x0A -> Some 'n'
  | 0x0D -> Some 'r'
  | 0x09 -> Some 't'
  | 0x0B -> Some 'v'
  | _ -> None

let regexp_escape_is_other_punctuator = function
  | 0x2C | 0x2D | 0x3D | 0x3C | 0x3E | 0x23 | 0x26 | 0x21 | 0x25 | 0x3A
  | 0x3B | 0x40 | 0x7E | 0x27 | 0x60 | 0x22 -> true
  | _ -> false

let regexp_escape_is_surrogate code_point =
  is_high_surrogate code_point || is_low_surrogate code_point

let regexp_escape_utf16_units_of_code_point code_point =
  if code_point > 0xFFFF then
    let high, low = utf16_surrogates_of_code_point code_point in
    [ high; low ]
  else [ code_point ]

let regexp_escape_encode_code_point add_code_point buffer code_point =
  if regexp_escape_is_syntax_character code_point || code_point = 0x2F then begin
    Buffer.add_char buffer '\\';
    add_code_point buffer code_point
  end
  else
    match regexp_escape_control_escape_char code_point with
    | Some escaped ->
      Buffer.add_char buffer '\\';
      Buffer.add_char buffer escaped
    | None ->
      if
        regexp_escape_is_other_punctuator code_point
        || is_ecma_whitespace_or_line_terminator_code code_point
        || regexp_escape_is_surrogate code_point
      then begin
        if code_point <= 0xFF then regexp_escape_add_x_escape buffer code_point
        else
          List.iter
            (regexp_escape_add_unicode_escape buffer)
            (regexp_escape_utf16_units_of_code_point code_point)
      end
      else add_code_point buffer code_point

let regexp_escape_with add_code_point value =
  let buffer = Buffer.create (String.length value) in
  let rec loop index escaped_empty =
    match ecma_decode_next ~unicode:true value index with
    | None -> Buffer.contents buffer
    | Some (next_index, code_point) ->
      if
        escaped_empty
        && (is_ascii_digit_code code_point
            || regexp_escape_is_ascii_letter_code code_point)
      then regexp_escape_add_x_escape buffer code_point
      else regexp_escape_encode_code_point add_code_point buffer code_point;
      loop next_index false
  in
  loop 0 true

let escape value = regexp_escape_with add_utf8_code_point value

let escape_js (Js_string value) =
  Js_string (regexp_escape_with add_utf16_encoded_code_point_to_storage value)

let ecma_decode_previous ?(unicode = false) value index =
  match utf8_decode_previous value index with
  | Some (low_index, low) when unicode && is_low_surrogate low ->
    (match utf8_decode_previous value low_index with
     | Some (high_index, high) when is_high_surrogate high ->
       Some (high_index, combine_surrogates high low)
     | _ -> Some (low_index, low))
  | result -> result

let utf16_code_unit_count_of_code_point code_point =
  if code_point > 0xFFFF then 2 else 1

let utf16_code_unit_index_of_utf8_byte_index value byte_index =
  let length = String.length value in
  let rec loop index code_units =
    if index >= byte_index || index >= length then code_units
    else
      match utf8_decode_next value index with
      | None -> code_units
      | Some (next_index, code_point) ->
        if next_index > byte_index then code_units
        else
          loop next_index
            (code_units + utf16_code_unit_count_of_code_point code_point)
  in
  loop 0 0

let utf16_code_unit_length_of_utf8 value =
  utf16_code_unit_index_of_utf8_byte_index value (String.length value)

let utf8_byte_index_of_utf16_code_unit_index value code_unit_index =
  let length = String.length value in
  let rec loop index code_units =
    if index >= length || code_units >= code_unit_index then index
    else
      match utf8_decode_next value index with
      | None -> min length (index + max 0 (code_unit_index - code_units))
      | Some (next_index, code_point) ->
        let width = utf16_code_unit_count_of_code_point code_point in
        if code_units + width > code_unit_index then index
        else loop next_index (code_units + width)
  in
  if code_unit_index <= 0 then 0 else loop 0 0

let utf16_code_unit_width_at_index value code_unit_index =
  let byte_index = utf8_byte_index_of_utf16_code_unit_index value code_unit_index in
  match utf8_decode_next value byte_index with
  | Some (_next_index, code_point) when code_point > 0xFFFF -> 2
  | Some (next_index, high) when is_high_surrogate high ->
    (match utf8_decode_next value next_index with
     | Some (_after_low, low) when is_low_surrogate low -> 2
     | _ -> 1)
  | Some _ -> 1
  | None -> 1

let advance_string_index input index unicode =
  if not unicode then index + 1
  else
    let input_length = utf16_code_unit_length_of_utf8 input in
    if index + 1 >= input_length then index + 1
    else index + utf16_code_unit_width_at_index input index

let match_result_of_byte_range input start_index end_index =
  {
    start_index = utf16_code_unit_index_of_utf8_byte_index input start_index;
    end_index = utf16_code_unit_index_of_utf8_byte_index input end_index;
    matched_text = String.sub input start_index (end_index - start_index);
  }

let utf8_substring_by_utf16_code_units input start_index end_index =
  let start_byte_index =
    utf8_byte_index_of_utf16_code_unit_index input start_index
  in
  let end_byte_index =
    utf8_byte_index_of_utf16_code_unit_index input end_index
  in
  String.sub input start_byte_index (end_byte_index - start_byte_index)

let text_of_capture_range input = function
  | None -> None
  | Some range ->
    Some
      (String.sub
         input
         range.range_start_index
         (range.range_end_index - range.range_start_index))

let advance_search_byte_index flags input index =
  if has_unicode_semantics flags then
    match ecma_decode_next ~unicode:true input index with
    | Some (next_index, _) when next_index > index -> next_index
    | _ -> index + 1
  else
    match utf8_decode_next input index with
    | Some (next_index, _) when next_index > index -> next_index
    | _ -> index + 1

let consume_if_matches direction state continuation predicate =
  match direction with
  | Forward ->
    if
      state.index < String.length state.input
      && predicate state.input.[state.index]
    then continuation { state with index = state.index + 1 }
    else None
  | Backward ->
    if state.index > 0 && predicate state.input.[state.index - 1] then
      continuation { state with index = state.index - 1 }
    else None

let consume_code_unit_if_matches direction state continuation predicate =
  match direction with
  | Forward ->
    (match utf8_decode_next state.input state.index with
     | Some (next_index, code_unit) when predicate code_unit ->
       continuation { state with index = next_index }
     | _ -> None)
  | Backward ->
    (match utf8_decode_previous state.input state.index with
     | Some (previous_index, code_unit) when predicate code_unit ->
       continuation { state with index = previous_index }
     | _ -> None)

let consume_code_point_if_matches ~unicode direction state continuation predicate =
  match direction with
  | Forward ->
    (match ecma_decode_next ~unicode state.input state.index with
     | Some (next_index, code_point) when predicate code_point ->
       continuation { state with index = next_index }
     | _ -> None)
  | Backward ->
    (match ecma_decode_previous ~unicode state.input state.index with
     | Some (previous_index, code_point) when predicate code_point ->
       continuation { state with index = previous_index }
     | _ -> None)

let unicode_property_escape_is_negated source =
  String.length source >= 2 && source.[1] = 'P'

let unicode_character_property_escape_matches source code_point =
  let body =
    match unicode_property_escape_body source with
    | Some body -> body
    | None -> unsupported_match_engine ("Unicode property escape " ^ source)
  in
  let matches =
    match String.split_on_char '=' body with
    | [ ("General_Category" | "gc"); value ] ->
      Ecma_regex_ucd_tables.general_category_matches value code_point
    | [ ("Script" | "sc"); value ] ->
      Ecma_regex_ucd_tables.script_matches value code_point
    | [ ("Script_Extensions" | "scx"); value ] ->
      Ecma_regex_ucd_tables.script_extensions_matches value code_point
    | [ value ] ->
      (match Ecma_regex_ucd_tables.general_category_value_canonical_name value with
       | Some _ -> Ecma_regex_ucd_tables.general_category_matches value code_point
       | None ->
         (match Ecma_regex_ucd_tables.binary_property_canonical_name value with
          | Some _ -> Ecma_regex_ucd_tables.binary_property_matches value code_point
          | None -> unsupported_match_engine ("Unicode property escape " ^ source)))
    | _ -> unsupported_match_engine ("Unicode property escape " ^ source)
  in
  if unicode_property_escape_is_negated source then not matches else matches

type unicode_character_class_element =
  | Unicode_class_code_point of int
  | Unicode_class_ranges of (int * int) list
  | Unicode_class_predicate of (int -> bool)

let code_point_ranges_for_positive_class_escape escaped =
  match escaped with
  | 'd' -> Some [ (Char.code '0', Char.code '9') ]
  | 's' -> Some ecma_whitespace_or_line_terminator_ranges
  | 'w' ->
    Some
      [
        (Char.code '0', Char.code '9');
        (Char.code 'A', Char.code 'Z');
        (Char.code '_', Char.code '_');
        (Char.code 'a', Char.code 'z');
      ]
  | _ -> None

let unicode_character_class_escape_matches flags source code_point =
  match source with
  | "\\d" -> is_ascii_digit_code code_point
  | "\\D" -> not (is_ascii_digit_code code_point)
  | "\\s" -> is_ecma_whitespace_or_line_terminator_code code_point
  | "\\S" -> not (is_ecma_whitespace_or_line_terminator_code code_point)
  | "\\w" -> is_word_code_point flags code_point
  | "\\W" -> not (is_word_code_point flags code_point)
  | _ -> unsupported_match_engine ("character class escape " ^ source)

let ensure_class_escape_within_stop source stop next_index =
  if next_index <= stop then ()
  else unsupported_match_engine ("unterminated character class escape in " ^ source)

let parse_legacy_unicode_class_control_escape flags source stop index =
  if
    flags.unicode
    || flags.unicode_sets
    || index + 1 >= stop
    || source.[index] <> '\\'
    || source.[index + 1] <> 'c'
  then None
  else if index + 2 < stop then
    match annex_b_class_control_escape_code source.[index + 2] with
    | Some code -> Some (index + 3, Unicode_class_code_point code)
    | None -> Some (index + 1, Unicode_class_code_point (Char.code '\\'))
  else Some (index + 1, Unicode_class_code_point (Char.code '\\'))

let parse_unicode_class_element flags source stop index =
  if index >= stop then unsupported_match_engine "empty character class element"
  else if source.[index] = '\\' then
    if index + 1 >= stop then unsupported_match_engine "unterminated class escape"
    else if source.[index + 1] = 'b' then
      (index + 2, Unicode_class_code_point 0x08)
    else
      match parse_legacy_unicode_class_control_escape flags source stop index with
      | Some result -> result
      | None ->
        (match parse_escape flags source index with
         | Ok (next_index, Unicode_property_escape property_source) ->
           ensure_class_escape_within_stop source stop next_index;
           ( next_index,
             Unicode_class_predicate
               (unicode_character_property_escape_matches property_source) )
         | Ok (next_index, Character_class_escape escape_source) ->
           ensure_class_escape_within_stop source stop next_index;
           (match escape_source with
            | "\\d" | "\\s" | "\\w" ->
              let escaped = escape_source.[1] in
              (match code_point_ranges_for_positive_class_escape escaped with
               | Some ranges -> (next_index, Unicode_class_ranges ranges)
               | None ->
                 unsupported_match_engine
                   ("character class escape " ^ escape_source))
            | "\\D" | "\\S" | "\\W" ->
              ( next_index,
                Unicode_class_predicate
                  (unicode_character_class_escape_matches flags escape_source) )
            | _ ->
              unsupported_match_engine ("character class escape " ^ escape_source))
         | Ok (next_index, Literal_code_point code_point) ->
           ensure_class_escape_within_stop source stop next_index;
           (next_index, Unicode_class_code_point code_point)
         | Ok (_, Assertion_escape _)
         | Ok (_, Decimal_escape _)
         | Ok (_, Named_backreference _)
         | Ok (_, Dot)
         | Ok (_, Character_class _)
         | Ok (_, Capturing_group _)
         | Ok (_, Named_capture_group _)
         | Ok (_, Noncapturing_group _)
         | Ok (_, Positive_lookahead _)
         | Ok (_, Negative_lookahead _)
         | Ok (_, Positive_lookbehind _)
         | Ok (_, Negative_lookbehind _)
         | Ok (_, Start_anchor)
         | Ok (_, End_anchor)
         | Ok (_, Modifiers_group _)
         | Ok (_, Quantified _) ->
           unsupported_match_engine "character class escape"
         | Error message -> unsupported_match_engine message)
  else
    match utf8_decode_next source index with
    | Some (next_index, code_point) when next_index <= stop ->
      (next_index, Unicode_class_code_point code_point)
    | _ -> unsupported_match_engine "invalid character class code point"

let unicode_character_class_elements ?trace flags source =
  let length = String.length source in
  if length < 2 || source.[0] <> '[' || source.[length - 1] <> ']' then
    unsupported_match_engine "malformed character class";
  let inverted = length >= 3 && source.[1] = '^' in
  let start = if inverted then 2 else 1 in
  let stop = length - 1 in
  let rec loop index elements =
    if index >= stop then (inverted, List.rev elements)
    else
      let next_index, element =
        parse_unicode_class_element flags source stop index
      in
      match element with
      | Unicode_class_code_point first
        when next_index < stop
             && source.[next_index] = '-'
             && next_index + 1 < stop ->
        let after_range, range_end =
          parse_unicode_class_element flags source stop (next_index + 1)
        in
        (match range_end with
         | Unicode_class_code_point last when first <= last ->
           observe_character_range trace;
           loop after_range (Unicode_class_ranges [ (first, last) ] :: elements)
         | Unicode_class_code_point _ ->
           unsupported_match_engine "invalid character class range"
         | Unicode_class_ranges _
         | Unicode_class_predicate _ ->
           unsupported_match_engine "class escape as range endpoint")
      | _ -> loop next_index (element :: elements)
  in
  loop start []

let code_point_in_range code_point (first, last) =
  first <= code_point && code_point <= last

let unicode_character_class_element_matches flags element code_point =
  match element with
  | Unicode_class_code_point expected ->
    List.exists (( = ) expected) (code_point_case_variants flags code_point)
  | Unicode_class_ranges ranges ->
    List.exists
      (fun candidate -> List.exists (code_point_in_range candidate) ranges)
      (code_point_case_variants flags code_point)
  | Unicode_class_predicate predicate -> predicate code_point

let unicode_character_class_matches ?trace flags source code_point =
  let inverted, elements = unicode_character_class_elements ?trace flags source in
  let member =
    List.exists
      (fun element ->
         unicode_character_class_element_matches flags element code_point)
      elements
  in
  if inverted then begin
    observe_character_complement_operation trace;
    let in_universe =
      allcharacters_contains_code_point ?trace flags code_point
    in
    let result = in_universe && not member in
    observe_character_complement_difference trace;
    result
  end
  else member

let start_anchor_matches flags state =
  state.index = 0
  || (flags.multiline
      && state.index > 0
      &&
      match utf8_decode_previous state.input state.index with
      | Some (_, code_unit) -> is_line_terminator_code_point code_unit
      | None -> false)

let end_anchor_matches flags state =
  let input_length = String.length state.input in
  state.index = input_length
  || (flags.multiline
      && state.index < input_length
      &&
      match utf8_decode_next state.input state.index with
      | Some (_, code_unit) -> is_line_terminator_code_point code_unit
      | None -> false)

let is_word_char_at_byte_index flags input index =
  index >= 0
  && index < String.length input
  &&
  match utf8_decode_next input index with
  | Some (_, code_point) -> is_word_code_point flags code_point
  | None -> false

let is_word_char_before_byte_index flags input index =
  match utf8_decode_previous input index with
  | Some (_, code_point) -> is_word_code_point flags code_point
  | None -> false

let word_boundary_matches flags state =
  let previous = is_word_char_before_byte_index flags state.input state.index in
  let current = is_word_char_at_byte_index flags state.input state.index in
  previous <> current

let backreference_chars_equal flags left right =
  canonicalize_ascii flags left = canonicalize_ascii flags right

let literal_code_point_matches_code flags expected actual =
  canonicalize_code_point flags expected = canonicalize_code_point flags actual

let literal_code_point_matches flags code_point char =
  let expected = byte_of_code_point code_point in
  literal_code_point_matches_code flags (Char.code expected) (Char.code char)

let string_contains_char value char =
  String.exists (( = ) char) value

let update_modifier_flag modifiers char current =
  if string_contains_char modifiers.remove_modifiers char then false
  else if string_contains_char modifiers.add_modifiers char then true
  else current

let apply_regexp_modifiers flags modifiers =
  {
    flags with
    ignore_case =
      update_modifier_flag modifiers 'i' flags.ignore_case;
    multiline =
      update_modifier_flag modifiers 'm' flags.multiline;
    dot_all =
      update_modifier_flag modifiers 's' flags.dot_all;
  }

let captured_range_matches flags input captured_start compare_start length =
  let rec loop offset =
    if offset = length then true
    else
      backreference_chars_equal flags
        input.[captured_start + offset]
        input.[compare_start + offset]
      && loop (offset + 1)
  in
  loop 0

let match_captured_range direction flags state continuation range =
  let length = range.range_end_index - range.range_start_index in
  if length < 0 then unsupported_match_engine "capture range"
  else begin
    observe_backreference_range_read direction state;
    let next_index =
      match direction with
      | Forward -> state.index + length
      | Backward -> state.index - length
    in
    let input_length = String.length state.input in
    if next_index < 0 || next_index > input_length then begin
      observe_backreference_bounds_failure state;
      None
    end
    else
      let compare_start = min state.index next_index in
      observe_backreference_compare_start state;
      if length > 0 then observe_backreference_canonicalize_compare state;
      if
        captured_range_matches flags state.input range.range_start_index
          compare_start length
      then begin
        let next_state = { state with index = next_index } in
        observe_backreference_result_state state;
        observe_backreference_continuation_return state;
        continuation next_state
      end
      else None
  end

let match_backreference_indices direction flags indices state continuation =
  observe_backreference_matcher_entry state;
  let rec first_defined = function
    | [] ->
      observe_backreference_undefined_capture_continuation state;
      observe_backreference_continuation_return state;
      continuation state
    | capture_index :: rest ->
      observe_backreference_ns_iteration state;
      if capture_index < 0 || capture_index >= Array.length state.captures then
        unsupported_match_engine "backreference capture index"
      else
        match state.captures.(capture_index) with
        | None -> first_defined rest
        | Some range ->
          observe_backreference_defined_capture state;
          match_captured_range direction flags state continuation range
  in
  first_defined indices

type repeat_bounds = {
  min_repetitions : int;
  max_repetitions : int option;
  repeat_greedy : bool;
}

let parse_braced_bounds source =
  let length = String.length source in
  if length < 3 || source.[0] <> '{' || source.[length - 1] <> '}' then
    unsupported_match_engine ("quantifier " ^ source)
  else
    let body = String.sub source 1 (length - 2) in
    match String.split_on_char ',' body with
    | [ exact ] ->
      let count = int_of_string exact in
      (count, Some count)
    | [ minimum; "" ] ->
      (int_of_string minimum, None)
    | [ minimum; maximum ] ->
      (int_of_string minimum, Some (int_of_string maximum))
    | _ -> unsupported_match_engine ("quantifier " ^ source)

let bounds_of_quantifier quantifier =
  let min_repetitions, max_repetitions =
    match quantifier.prefix with
    | Zero_or_more -> (0, None)
    | One_or_more -> (1, None)
    | Zero_or_one -> (0, Some 1)
    | Braced_quantifier source -> parse_braced_bounds source
  in
  {
    min_repetitions;
    max_repetitions;
    repeat_greedy = quantifier.greedy;
  }

let repeat_max_allows_more max_repetitions count =
  match max_repetitions with
  | None -> true
  | Some max -> count < max

let clear_quantified_captures capture_indices captures =
  match capture_indices with
  | [] -> captures
  | _ ->
    let copy = Array.copy captures in
    List.iter
      (fun index ->
         if index >= 0 && index < Array.length copy then copy.(index) <- None
         else unsupported_match_engine "capture index")
      capture_indices;
    copy

let capture_range_for direction x y =
  match direction with
  | Forward ->
    {
      range_start_index = x.index;
      range_end_index = y.index;
    }
  | Backward ->
    {
      range_start_index = y.index;
      range_end_index = x.index;
    }

let write_capture capture_index range captures =
  if capture_index < 0 || capture_index >= Array.length captures then
    unsupported_match_engine "capture index"
  else captures.(capture_index) <- Some range

let append_named_capture name index acc =
  let rec loop prefix = function
    | [] -> List.rev_append prefix [ (name, [ index ]) ]
    | (candidate, indices) :: rest when String.equal candidate name ->
      List.rev_append prefix ((candidate, indices @ [ index ]) :: rest)
    | pair :: rest -> loop (pair :: prefix) rest
  in
  loop [] acc

let rec named_capture_indices_ast = function
  | Disjunction alternatives ->
    List.fold_left
      (fun acc atoms -> named_capture_indices_alternative acc atoms)
      []
      alternatives

and named_capture_indices_alternative acc atoms =
  List.fold_left named_capture_indices_atom acc atoms

and named_capture_indices_atom acc = function
  | Named_capture_group (name, capture_index, ast) ->
    named_capture_indices_ast ast
    |> List.fold_left
         (fun acc (nested_name, indices) ->
            List.fold_left
              (fun acc index -> append_named_capture nested_name index acc)
              acc
              indices)
         (append_named_capture name capture_index acc)
  | Capturing_group (_, ast)
  | Noncapturing_group ast
  | Positive_lookahead ast
  | Negative_lookahead ast
  | Positive_lookbehind ast
  | Negative_lookbehind ast
  | Modifiers_group (_, ast) ->
    named_capture_indices_ast ast
    |> List.fold_left
         (fun acc (name, indices) ->
            List.fold_left
              (fun acc index -> append_named_capture name index acc)
              acc
              indices)
         acc
  | Quantified (atom, _) -> named_capture_indices_atom acc atom
  | Literal_code_point _
  | Dot
  | Character_class _
  | Character_class_escape _
  | Start_anchor
  | End_anchor
  | Assertion_escape _
  | Unicode_property_escape _
  | Named_backreference _
  | Decimal_escape _ ->
    acc

let named_backreference_indices name named_indices =
  match List.assoc_opt name named_indices with
  | Some indices -> indices
  | None -> unsupported_match_engine "named backreference target"

let decimal_backreference_indices value capture_count =
  match parse_positive_decimal value with
  | Some index when index >= 1 && index <= capture_count -> [ index - 1 ]
  | _ -> unsupported_match_engine "decimal escape"

let literal_code_point_requires_code_point_matcher flags code_point =
  code_point > 0x7F || (flags.ignore_case && has_unicode_semantics flags)

let rec matcher_of_atom direction flags named_indices capture_count = function
  | Literal_code_point code_point ->
    if literal_code_point_requires_code_point_matcher flags code_point then
      fun state continuation ->
        consume_code_point_if_matches
          ~unicode:(has_unicode_semantics flags)
          direction
          state
          continuation
          (literal_code_point_matches_code flags code_point)
    else
      fun state continuation ->
        consume_if_matches direction state continuation
          (literal_code_point_matches flags code_point)
  | Dot ->
    if has_unicode_semantics flags then
      fun state continuation ->
        consume_code_point_if_matches ~unicode:true direction state continuation
          (fun code_point ->
             flags.dot_all || not (is_line_terminator_code_point code_point))
    else
      fun state continuation ->
        consume_code_unit_if_matches direction state continuation
          (fun code_unit ->
             flags.dot_all || not (is_line_terminator_code_point code_unit))
  | Character_class source ->
    if flags.unicode_sets && character_class_contains_class_string_disjunction source
    then unicode_sets_string_element_matcher direction flags source
    else if character_class_requires_code_point_matcher source then
      fun state continuation ->
        consume_code_point_if_matches
          ~unicode:(has_unicode_semantics flags)
          direction
          state
          continuation
          (unicode_character_class_matches ?trace:state.trace flags source)
    else if has_unicode_semantics flags then
      fun state continuation ->
        consume_code_point_if_matches ~unicode:true direction state continuation
          (character_class_matches_code_unit ?trace:state.trace flags source)
    else
      fun state continuation ->
        consume_code_unit_if_matches direction state continuation
          (character_class_matches_code_unit ?trace:state.trace flags source)
  | Character_class_escape source ->
    if has_unicode_semantics flags then
      fun state continuation ->
        consume_code_point_if_matches ~unicode:true direction state continuation
          (unicode_character_class_escape_matches flags source)
    else
      fun state continuation ->
        consume_code_unit_if_matches direction state continuation
          (unicode_character_class_escape_matches flags source)
  | Capturing_group (capture_index, ast)
  | Named_capture_group (_, capture_index, ast) ->
    let group_matcher =
      matcher_of_disjunction direction flags named_indices capture_count ast
    in
    fun state continuation ->
      observe_capture_matcher_invocation state;
      let nested_continuation y =
        let cap = Array.copy y.captures in
        let range = capture_range_for direction state y in
        write_capture capture_index range cap;
        observe_capture_nested_continuation
          direction capture_index state y cap range;
        let z = { input = state.input; index = y.index; captures = cap; trace = state.trace } in
        observe_capture_result_state state z;
        observe_capture_outer_continuation state;
        continuation z
      in
      observe_capture_submatcher_invocation state;
      group_matcher state nested_continuation
  | Noncapturing_group _ ->
    fun _ _ -> unsupported_match_engine "noncapturing group"
  | Positive_lookahead ast ->
    let assertion_matcher =
      matcher_of_disjunction Forward flags named_indices capture_count ast
    in
    fun state continuation ->
      (match assertion_matcher state (fun y -> Some y) with
       | None -> None
       | Some result_state ->
         continuation
           {
             input = state.input;
             index = state.index;
             captures = result_state.captures;
             trace = state.trace;
           })
  | Negative_lookahead ast ->
    let assertion_matcher =
      matcher_of_disjunction Forward flags named_indices capture_count ast
    in
    fun state continuation ->
      (match assertion_matcher state (fun y -> Some y) with
       | Some _ -> None
       | None -> continuation state)
  | Positive_lookbehind ast ->
    let assertion_matcher =
      matcher_of_disjunction Backward flags named_indices capture_count ast
    in
    fun state continuation ->
      (match assertion_matcher state (fun y -> Some y) with
       | None -> None
       | Some result_state ->
         continuation
           {
             input = state.input;
             index = state.index;
             captures = result_state.captures;
             trace = state.trace;
           })
  | Negative_lookbehind ast ->
    let assertion_matcher =
      matcher_of_disjunction Backward flags named_indices capture_count ast
    in
    fun state continuation ->
      (match assertion_matcher state (fun y -> Some y) with
       | Some _ -> None
       | None -> continuation state)
  | Start_anchor ->
    fun state continuation ->
      if start_anchor_matches flags state then continuation state else None
  | End_anchor ->
    fun state continuation ->
      if end_anchor_matches flags state then continuation state else None
  | Assertion_escape "\\b" ->
    fun state continuation ->
      if word_boundary_matches flags state then continuation state else None
  | Assertion_escape "\\B" ->
    fun state continuation ->
      if word_boundary_matches flags state then None else continuation state
  | Assertion_escape source ->
    fun _ _ -> unsupported_match_engine ("assertion escape " ^ source)
  | Unicode_property_escape source ->
    if flags.unicode_sets && unicode_property_escape_may_contain_strings source
    then
      unicode_sets_escape_string_element_matcher direction flags source
    else
      fun state continuation ->
        consume_code_point_if_matches
          ~unicode:(has_unicode_semantics flags)
          direction
          state
          continuation
          (unicode_character_property_escape_matches source)
  | Named_backreference name ->
    let indices = named_backreference_indices name named_indices in
    fun state continuation ->
      observe_named_backreference_model state;
      match_backreference_indices direction flags indices state continuation
  | Decimal_escape value ->
    let indices = decimal_backreference_indices value capture_count in
    fun state continuation ->
      observe_decimal_backreference_model state;
      match_backreference_indices direction flags indices state continuation
  | Modifiers_group (modifiers, ast) ->
    let modified_flags = apply_regexp_modifiers flags modifiers in
    matcher_of_disjunction direction modified_flags named_indices capture_count ast
  | Quantified (atom, quantifier) ->
    let atom_matcher =
      matcher_of_atom direction flags named_indices capture_count atom
    in
    let bounds = bounds_of_quantifier quantifier in
    let capture_indices = capture_indices_atom atom in
    let rec repeat count state continuation =
      let try_continuation () =
        if count >= bounds.min_repetitions then continuation state else None
      in
      let try_more () =
        if not (repeat_max_allows_more bounds.max_repetitions count) then None
        else
          let captures =
            clear_quantified_captures capture_indices state.captures
          in
          let repeat_state =
            if captures == state.captures then state else { state with captures }
          in
          atom_matcher repeat_state (fun next_state ->
            if next_state.index = state.index then
              let next_count = count + 1 in
              if next_count >= bounds.min_repetitions then continuation next_state
              else repeat next_count next_state continuation
            else repeat (count + 1) next_state continuation)
      in
      if bounds.repeat_greedy then
        match try_more () with
        | Some _ as result -> result
        | None -> try_continuation ()
      else
        match try_continuation () with
        | Some _ as result -> result
        | None -> try_more ()
    in
    fun state continuation -> repeat 0 state continuation

and matcher_of_atoms direction flags named_indices capture_count = function
  | [] -> fun state continuation -> continuation state
  | [ atom ] -> matcher_of_atom direction flags named_indices capture_count atom
  | atom :: rest ->
    let atom_matcher =
      matcher_of_atom direction flags named_indices capture_count atom
    in
    let rest_matcher =
      matcher_of_atoms direction flags named_indices capture_count rest
    in
    match_sequence direction atom_matcher rest_matcher

and match_sequence direction first second state continuation =
  match direction with
  | Forward ->
    observe_match_sequence_forward_entry state;
    first state (fun next_state ->
      observe_match_sequence_forward_nested_state next_state;
      second next_state continuation)
  | Backward ->
    observe_match_sequence_backward_entry state;
    second state (fun next_state ->
      observe_match_sequence_backward_nested_state next_state;
      first next_state continuation)

and match_two_alternatives first second state continuation =
  observe_match_two_alternatives state;
  match first state continuation with
  | Some _ as result -> result
  | None -> second state continuation

and matcher_of_alternatives direction flags named_indices capture_count = function
  | [] -> fun _ _ -> None
  | [ atoms ] -> matcher_of_atoms direction flags named_indices capture_count atoms
  | atoms :: rest ->
    match_two_alternatives
      (matcher_of_atoms direction flags named_indices capture_count atoms)
      (matcher_of_alternatives direction flags named_indices capture_count rest)

and matcher_of_disjunction direction flags named_indices capture_count = function
  | Disjunction alternatives ->
    matcher_of_alternatives direction flags named_indices capture_count alternatives

let match_disjunction_state_at ?trace ?(direction = Forward) flags input index ast =
  let capture_count = count_captures_ast ast in
  let named_indices = named_capture_indices_ast ast in
  let matcher = matcher_of_disjunction direction flags named_indices capture_count ast in
  let state = { input; index; captures = Array.make capture_count None; trace } in
  let final_continuation state = Some state in
  match matcher state final_continuation with
  | None -> None
  | Some state ->
    let start_index, end_index =
      match direction with
      | Forward -> (index, state.index)
      | Backward -> (state.index, index)
    in
    Some (start_index, end_index, state)

let match_disjunction_at ?trace ?(direction = Forward) flags input index ast =
  match match_disjunction_state_at ?trace ~direction flags input index ast with
  | None -> None
  | Some (start_index, end_index, _state) ->
    Some (match_result_of_byte_range input start_index end_index)

let exec_ast_state_from_byte_index ?trace flags ast input start_index =
  let length = String.length input in
  if flags.sticky then
    if start_index > length then None
    else match_disjunction_state_at ?trace flags input start_index ast
  else
    let rec loop index =
      if index > length then None
      else
        match match_disjunction_state_at ?trace flags input index ast with
        | Some _ as result -> result
        | None -> loop (advance_search_byte_index flags input index)
    in
    loop start_index

let exec_ast_state ?trace flags ast input =
  exec_ast_state_from_byte_index ?trace flags ast input 0

let exec_ast ?trace flags ast input =
  match exec_ast_state ?trace flags ast input with
  | None -> None
  | Some (start_index, end_index, _state) ->
    Some (match_result_of_byte_range input start_index end_index)

let match_result_range_valid input result =
  0 <= result.start_index
  && result.start_index <= result.end_index
  && result.end_index <= utf16_code_unit_length_of_utf8 input

let ascii_only source =
  let rec loop index =
    index = String.length source
    || (Char.code source.[index] <= 0x7f && loop (index + 1))
  in
  loop 0

let inspect_spec_model ?(model_scenario = "default") source =
  let source_character_fixture_is_ascii = ascii_only source in
  let observed_model_fields =
    match model_scenario with
    | "lexical_grammar_source_model" ->
      [|
        "lexical_grammar_source_character_goal_model_observed";
        "source_character_code_point_model_observed";
        "source_character_utf16_code_unit_fixture_observed";
      |]
    | "syntactic_token_stream_policy" ->
      [| "syntactic_token_stream_boundary_policy_observed" |]
    | "regexp_grammar_pattern_model" ->
      [|
        "regexp_grammar_pattern_source_model_observed";
        "source_character_code_point_model_observed";
        "source_character_utf16_code_unit_fixture_observed";
      |]
    | "grammar_notation_boundary_model" ->
      [| "lexical_regexp_grammar_notation_boundary_observed" |]
    | _ -> [| "spec_model_observed" |]
  in
  let observed field =
    Array.exists (( = ) field) observed_model_fields
  in
  {
    observed_model_fields;
    source_text = source;
    source_character_fixture_is_ascii;
    source_code_point_count = String.length source;
    source_utf16_code_unit_length = String.length source;
    source_character_code_point_model_observed =
      source_character_fixture_is_ascii
      && observed "source_character_code_point_model_observed";
    source_character_utf16_code_unit_fixture_observed =
      source_character_fixture_is_ascii
      && observed "source_character_utf16_code_unit_fixture_observed";
    lexical_grammar_terminal_model_observed =
      observed "lexical_grammar_source_character_goal_model_observed";
    lexical_grammar_goal_symbols_observed =
      observed "lexical_grammar_source_character_goal_model_observed";
    syntactic_token_stream_policy_observed =
      observed "syntactic_token_stream_boundary_policy_observed";
    regexp_grammar_terminal_model_observed =
      observed "regexp_grammar_pattern_source_model_observed";
    regexp_grammar_pattern_goal_observed =
      observed "regexp_grammar_pattern_source_model_observed";
    regexp_grammar_translates_to_pattern_observed =
      observed "regexp_grammar_pattern_source_model_observed";
    grammar_double_colon_notation_observed =
      observed "lexical_regexp_grammar_notation_boundary_observed";
    grammar_shared_productions_policy_observed =
      observed "lexical_regexp_grammar_notation_boundary_observed";
    lexical_grammar_goal_symbols =
      [|
        "InputElementDiv";
        "InputElementTemplateTail";
        "InputElementRegExp";
        "InputElementRegExpOrTemplateTail";
        "InputElementHashbangOrRegExp";
      |];
    regexp_grammar_goal_symbol = "Pattern";
    regexp_grammar_clause = "22.2.1";
  }

let inspect_exec_result_instance_model (Compiled (source, flags, _ast)) =
  let internal_slots =
    [|
      "[[OriginalSource]]";
      "[[OriginalFlags]]";
      "[[RegExpRecord]]";
      "[[RegExpMatcher]]";
    |]
  in
  {
    observed_model_fields =
      [|
        "regexp_instance_internal_slots_observed";
        "regexp_instance_last_index_property_observed";
        "last_index_integral_start_property_attributes_observed";
      |];
    original_source = source;
    original_flags = flags_to_string flags;
    internal_slots;
    original_source_slot_observed = true;
    original_flags_slot_observed = true;
    regexp_record_slot_observed = true;
    regexp_matcher_slot_observed = true;
    regexp_matcher_closure_observed = true;
    last_index_property_observed = true;
    last_index_initial_value = 0;
    last_index_start_index_observed = true;
    last_index_integral_number_coercion_observed = true;
    last_index_writable = true;
    last_index_enumerable = false;
    last_index_configurable = false;
  }

let inspect_exec_result_exec_model (Compiled (_source, flags, ast)) input =
  let exec_result =
    match exec_ast_state flags ast input with
    | None -> None
    | Some (start_index, end_index, _state) ->
      Some (match_result_of_byte_range input start_index end_index)
  in
  let test_result = Option.is_some exec_result in
  let match_record_range_valid =
    match exec_result with
    | None -> false
    | Some result -> match_result_range_valid input result
  in
  let get_match_string_result =
    match exec_result with
    | None -> None
    | Some result -> Some result.matched_text
  in
  let get_match_string_result_observed =
    match exec_result, get_match_string_result with
    | Some result, Some value -> value = result.matched_text
    | _ -> false
  in
  {
    regexp_prototype_exec_operation_observed = true;
    regexp_prototype_exec_result_shape_observed = true;
    regexp_prototype_exec_this_value_observed = true;
    regexp_prototype_exec_internal_slot_observed = true;
    regexp_prototype_exec_string_input_observed = true;
    regexp_prototype_exec_delegates_to_builtin_exec = true;
    regexp_prototype_test_operation_observed = true;
    regexp_prototype_test_this_value_observed = true;
    regexp_prototype_test_typed_receiver_enforced = true;
    regexp_prototype_test_string_input_observed = true;
    regexp_prototype_test_calls_regexp_exec = true;
    regexp_prototype_test_null_result_observed = not test_result;
    regexp_prototype_test_false_result_observed = not test_result;
    regexp_prototype_test_true_result_observed = test_result;
    match_record_observed = Option.is_some exec_result;
    match_record_fields_observed = Option.is_some exec_result;
    match_record_field_table_observed = Option.is_some exec_result;
    match_record_start_index_observed =
      (match exec_result with
       | None -> false
       | Some result -> result.start_index >= 0);
    match_record_end_index_observed =
      (match exec_result with
       | None -> false
       | Some result -> result.end_index >= result.start_index);
    match_record_range_valid;
    get_match_string_operation_observed = Option.is_some exec_result;
    get_match_string_range_assertion_observed = match_record_range_valid;
    get_match_string_result_observed;
    get_match_string_result;
    exec_result;
    test_result;
  }

let first_atom_of_ast (Disjunction alternatives) =
  let rec loop = function
    | [] -> None
    | [] :: rest -> loop rest
    | (atom :: _) :: _ -> Some atom
  in
  loop alternatives

let compile_atom_piecewise_dispatch_case_observed = function
  | Literal_code_point _
  | Dot
  | Character_class _
  | Character_class_escape _
  | Capturing_group _
  | Named_capture_group _
  | Noncapturing_group _
  | Positive_lookahead _
  | Negative_lookahead _
  | Positive_lookbehind _
  | Negative_lookbehind _
  | Start_anchor
  | End_anchor
  | Assertion_escape _
  | Unicode_property_escape _
  | Named_backreference _
  | Decimal_escape _
  | Modifiers_group _
  | Quantified _ ->
    true

let compile_atom_matcher_constructible flags ast atom =
  let capture_count = count_captures_ast ast in
  let named_indices = named_capture_indices_ast ast in
  try
    let _forward_matcher =
      matcher_of_atom Forward flags named_indices capture_count atom
    in
    let _backward_matcher =
      matcher_of_atom Backward flags named_indices capture_count atom
    in
    true
  with
  | Unsupported_match_engine _ -> false

let inspect_compile_atom_model (Compiled (_source, flags, ast)) =
  match first_atom_of_ast ast with
  | None ->
    {
      compile_atom_operation_shape_observed = false;
      compile_atom_piecewise_dispatch_observed = false;
    }
  | Some atom ->
    let matcher_constructible =
      compile_atom_matcher_constructible flags ast atom
    in
    {
      compile_atom_operation_shape_observed = matcher_constructible;
      compile_atom_piecewise_dispatch_observed =
        matcher_constructible
        && compile_atom_piecewise_dispatch_case_observed atom;
    }

let inspect_match_two_alternatives_model (Compiled (_source, flags, ast)) input =
  let trace = fresh_match_trace () in
  ignore (exec_ast ~trace flags ast input);
  observation_of_trace trace

let inspect_match_sequence_model (Compiled (_source, flags, ast)) input =
  let trace = fresh_match_trace () in
  ignore (exec_ast ~trace flags ast input);
  ignore
    (match_disjunction_at
       ~trace
       ~direction:Backward
       flags
       input
       (String.length input)
       ast);
  match_sequence_observation_of_trace trace

let inspect_character_class_model (Compiled (_source, flags, ast)) input =
  let trace = fresh_match_trace () in
  ignore (exec_ast ~trace flags ast input);
  character_class_observation_of_trace trace

let inspect_unicode_sets_string_element_model (Compiled (_source, flags, ast)) input =
  let trace = fresh_match_trace () in
  ignore (exec_ast ~trace flags ast input);
  unicode_sets_string_element_observation_of_trace trace

let inspect_capture_model (Compiled (_source, flags, ast)) input =
  let trace = fresh_match_trace () in
  ignore (match_disjunction_at ~trace ~direction:Forward flags input 0 ast);
  ignore
    (match_disjunction_at
       ~trace
       ~direction:Backward
       flags
       input
       (String.length input)
       ast);
  capture_observation_of_trace trace

let inspect_backreference_model (Compiled (_source, flags, ast)) input =
  let trace = fresh_match_trace () in
  ignore (match_disjunction_at ~trace ~direction:Forward flags input 0 ast);
  ignore
    (match_disjunction_at
       ~trace
       ~direction:Backward
       flags
       input
       (String.length input)
       ast);
  backreference_observation_of_trace trace

let inspect_backreference_matcher_model (Compiled (_source, flags, ast)) input =
  let trace = fresh_match_trace () in
  ignore (match_disjunction_at ~trace ~direction:Forward flags input 0 ast);
  ignore
    (match_disjunction_at
       ~trace
       ~direction:Backward
       flags
       input
       (String.length input)
       ast);
  backreference_matcher_observation_of_trace trace

let exec_result_capture_of_range input index = function
  | None ->
    {
      capture_index = index;
      capture_start_index = None;
      capture_end_index = None;
      captured_text = None;
    }
  | Some range ->
    {
      capture_index = index;
      capture_start_index = Some range.range_start_index;
      capture_end_index = Some range.range_end_index;
      captured_text =
        Some
          (String.sub
             input
             range.range_start_index
             (range.range_end_index - range.range_start_index));
    }

let capture_names_ast ast =
  let names = Array.make (count_captures_ast ast) None in
  let rec fill_ast = function
    | Disjunction alternatives -> List.iter fill_alternative alternatives
  and fill_alternative atoms =
    List.iter fill_atom atoms
  and fill_atom = function
    | Capturing_group (capture_index, ast) ->
      names.(capture_index) <- None;
      fill_ast ast
    | Named_capture_group (name, capture_index, ast) ->
      names.(capture_index) <- Some name;
      fill_ast ast
    | Noncapturing_group ast
    | Positive_lookahead ast
    | Negative_lookahead ast
    | Positive_lookbehind ast
    | Negative_lookbehind ast
    | Modifiers_group (_, ast) ->
      fill_ast ast
    | Quantified (atom, _) -> fill_atom atom
    | Literal_code_point _
    | Dot
    | Character_class _
    | Character_class_escape _
    | Start_anchor
    | End_anchor
    | Assertion_escape _
    | Unicode_property_escape _
    | Named_backreference _
    | Decimal_escape _ ->
      ()
  in
  fill_ast ast;
  names

let js_capture_of_range input capture_index = function
  | None ->
    {
      js_capture_index = capture_index + 1;
      js_capture_start_index = None;
      js_capture_end_index = None;
      js_capture_text = None;
    }
  | Some range ->
    {
      js_capture_index = capture_index + 1;
      js_capture_start_index =
        Some
          (utf16_code_unit_index_of_utf8_byte_index input
             range.range_start_index);
      js_capture_end_index =
        Some
          (utf16_code_unit_index_of_utf8_byte_index input
             range.range_end_index);
      js_capture_text =
        Some
          (Js_string
             (String.sub
                input
                range.range_start_index
                (range.range_end_index - range.range_start_index)));
    }

let js_captures_of_ranges input captures =
  captures |> Array.mapi (js_capture_of_range input) |> Array.to_list

let js_named_captures_of_ranges input ast captures =
  let names = capture_names_ast ast in
  let rec loop index acc =
    if index >= Array.length names then List.rev acc
    else
      match names.(index) with
      | None -> loop (index + 1) acc
      | Some name ->
        let js_named_capture =
          {
            js_named_capture_name = name;
            js_named_capture =
              js_capture_of_range input index captures.(index);
          }
        in
        loop (index + 1) (js_named_capture :: acc)
  in
  loop 0 []

let js_match_result_of_state input ast start_index end_index state =
  let result = match_result_of_byte_range input start_index end_index in
  {
    js_start_index = result.start_index;
    js_end_index = result.end_index;
    js_matched_text = Js_string result.matched_text;
    js_captures = js_captures_of_ranges input state.captures;
    js_named_captures =
      js_named_captures_of_ranges input ast state.captures;
  }

let index_pair_of_range = function
  | None -> None
  | Some range ->
    Some
      {
        index_pair_start_index = range.range_start_index;
        index_pair_end_index = range.range_end_index;
      }

let index_pair_range_valid input_length = function
  | None -> true
  | Some pair ->
    0 <= pair.index_pair_start_index
    && pair.index_pair_start_index <= pair.index_pair_end_index
    && pair.index_pair_end_index <= input_length

let array_exists predicate array =
  let rec loop index =
    index < Array.length array
    && (predicate array.(index) || loop (index + 1))
  in
  loop 0

let duplicate_group_name_observed group_names =
  let seen = Hashtbl.create 8 in
  array_exists
    (function
      | None -> false
      | Some name ->
        if Hashtbl.mem seen name then true
        else begin
          Hashtbl.add seen name ();
          false
        end)
    group_names

let add_unique field fields =
  if List.exists (String.equal field) fields then fields else field :: fields

let add_many fields acc =
  List.fold_right add_unique fields acc

let utf8_code_point_count value =
  let rec loop index count =
    match utf8_decode_next value index with
    | None -> count
    | Some (next_index, _) -> loop next_index (count + 1)
  in
  loop 0 0

let exec_result_of_state input = function
  | None -> None
  | Some (start_index, end_index, _state) ->
    Some (match_result_of_byte_range input start_index end_index)

let safe_exec_ast_state flags ast input =
  try exec_ast_state flags ast input with
  | Unsupported_match_engine _ -> None

let first_quantified_atom_info ast =
  let rec alternatives = function
    | [] -> None
    | atoms :: rest ->
      (match atoms_loop 0 atoms with
       | Some _ as found -> found
       | None -> alternatives rest)
  and atoms_loop captures_before = function
    | [] -> None
    | Quantified (atom, quantifier) :: _ ->
      let bounds = bounds_of_quantifier quantifier in
      Some
        ( captures_before,
          count_captures_atom atom,
          bounds.min_repetitions,
          bounds.max_repetitions,
          bounds.repeat_greedy )
    | atom :: rest ->
      atoms_loop (captures_before + count_captures_atom atom) rest
  in
  match ast with
  | Disjunction alternatives_list -> alternatives alternatives_list

let inspect_pattern_semantics_model ?(model_scenario = "default")
    (Compiled (_source, flags, ast)) input =
  let exec_result = safe_exec_ast_state flags ast input |> exec_result_of_state input in
  let input_length = String.length input in
  let input_code_point_count = utf8_code_point_count input in
  let input_utf16_code_unit_length = utf16_code_unit_length_of_utf8 input in
  let capture_count = count_captures_ast ast in
  let regexp_record_fields =
    [|
      "[[IgnoreCase]]";
      "[[Multiline]]";
      "[[DotAll]]";
      "[[Unicode]]";
      "[[UnicodeSets]]";
      "[[CapturingGroupsCount]]";
    |]
  in
  let
    ( quantified_paren_index,
      quantified_paren_count,
      quantifier_min,
      quantifier_max,
      quantifier_greedy )
    =
    match first_quantified_atom_info ast with
    | None -> (None, None, None, None, None)
    | Some
        ( paren_index,
          paren_count,
          min_repetitions,
          max_repetitions,
          repeat_greedy ) ->
      ( Some paren_index,
        Some paren_count,
        Some min_repetitions,
        max_repetitions,
        Some repeat_greedy )
  in
  let model_fields =
    [
      "pattern_semantics_model_observed";
      "regexp_record_model_observed";
      "regexp_record_ignore_case_field_observed";
      "regexp_record_multiline_field_observed";
      "regexp_record_dot_all_field_observed";
      "regexp_record_unicode_field_observed";
      "regexp_record_unicode_sets_field_observed";
      "regexp_record_capturing_groups_count_field_observed";
    ]
  in
  let unicode_fields =
    if model_scenario = "utf16_bmp_unicode_character_model" then
      [
        "bmp_pattern_definition_observed";
        "unicode_pattern_definition_observed";
        "utf16_bmp_character_model_observed";
        "unicode_code_point_character_model_observed";
        "source_character_list_model_observed";
        "non_bmp_source_utf16_encoding_model_observed";
      ]
    else []
  in
  let notation_fields =
    if model_scenario = "pattern_semantics_notation" then
      [
        "pattern_semantics_internal_data_structures_observed";
        "match_state_record_model_observed";
        "matcher_continuation_model_observed";
        "regexp_record_model_observed";
      ]
    else []
  in
  let record_fields =
    if model_scenario = "regexp_record_inventory" then
      [
        "regexp_record_inventory_observed";
        "regexp_record_fields_table_observed";
        "regexp_record_matcher_slot_observed";
        "regexp_record_original_flags_observed";
        "regexp_record_capture_count_observed";
      ]
    else []
  in
  let compile_pattern_fields =
    match model_scenario with
    | "compile_pattern_input_list" ->
      [
        "compile_pattern_input_list_assertion_observed";
        "compile_pattern_input_utf16_length_observed";
      ]
    | "compile_pattern_index" ->
      [
        "compile_pattern_index_bounds_assertion_observed";
        "compile_pattern_initial_index_observed";
      ]
    | "compile_pattern_continuation" ->
      [
        "compile_pattern_continuation_closure_observed";
        "compile_pattern_continuation_returns_match_state_observed";
      ]
    | "compile_pattern_match_state" ->
      [
        "compile_pattern_match_state_assertion_observed";
        "compile_pattern_match_state_input_preserved_observed";
        "compile_pattern_match_state_capture_slots_observed";
      ]
    | _ -> []
  in
  let compile_subpattern_fields =
    match model_scenario with
    | "compile_subpattern_operation" ->
      [
        "compile_subpattern_operation_model_observed";
        "compile_subpattern_direction_parameter_observed";
      ]
    | "compile_subpattern_piecewise_inventory" ->
      [
        "compile_subpattern_piecewise_inventory_observed";
        "compile_subpattern_disjunction_case_observed";
        "compile_subpattern_empty_case_observed";
        "compile_subpattern_sequence_case_observed";
        "compile_subpattern_assertion_case_observed";
        "compile_subpattern_atom_case_observed";
        "compile_subpattern_quantifier_case_observed";
      ]
    | _ -> []
  in
  let quantifier_fields =
    match model_scenario with
    | "quantifier_bounds_assert" ->
      if
        match quantifier_min, quantifier_max with
        | Some min, Some max -> min <= max
        | Some _, None -> true
        | _ -> false
      then [ "quantifier_bounds_assertion_observed" ]
      else []
    | "quantified_capture_index" ->
      [
        "quantified_paren_index_observed";
        "quantified_paren_count_observed";
        "quantified_capture_index_model_observed";
      ]
    | "quantified_repeat_closure" ->
      [
        "quantified_repeat_closure_observed";
        "quantified_repeat_match_state_parameter_observed";
        "quantified_repeat_continuation_parameter_observed";
        "quantified_repeat_captures_atom_and_quantifier_observed";
      ]
    | _ -> []
  in
  let empty_matcher_fields =
    match model_scenario with
    | "empty_matcher_state" ->
      [
        "empty_matcher_match_state_parameter_observed";
        "empty_matcher_continuation_parameter_observed";
      ]
    | _ -> []
  in
  {
    observed_model_fields =
      add_many model_fields []
      |> add_many unicode_fields
      |> add_many notation_fields
      |> add_many record_fields
      |> add_many compile_pattern_fields
      |> add_many compile_subpattern_fields
      |> add_many quantifier_fields
      |> add_many empty_matcher_fields
      |> List.rev
      |> Array.of_list;
    exec_result;
    input_length;
    input_code_point_count;
    input_utf16_code_unit_length;
    input_index = 0;
    capture_count;
    regexp_record_fields;
    quantifier_min;
    quantifier_max;
    quantifier_greedy;
    quantified_paren_index;
    quantified_paren_count;
  }

let inspect_exec_result_matching_model ?(model_scenario = "default_match")
    (Compiled (_source, flags, ast)) input =
  let normal_exec_result =
    match exec_ast_state flags ast input with
    | None -> None
    | Some (start_index, end_index, _state) ->
      Some (match_result_of_byte_range input start_index end_index)
  in
  let input_length = String.length input in
  let group_names = capture_names_ast ast in
  let has_groups = array_exists Option.is_some group_names in
  let last_index_before =
    match model_scenario with
    | "last_index_out_of_bounds_global" -> input_length + 1
    | "sticky_failure" -> 1
    | _ -> 0
  in
  let exec_result =
    match model_scenario with
    | "last_index_out_of_bounds_global" | "sticky_failure" -> None
    | _ -> normal_exec_result
  in
  let last_index_after =
    match model_scenario, exec_result with
    | ("last_index_out_of_bounds_global" | "sticky_failure"), None -> 0
    | "global_success", Some result -> result.end_index
    | _ -> last_index_before
  in
  let base_fields =
    [
      "regexp_exec_operation_observed";
      "regexp_exec_builtin_slot_required_observed";
      "regexp_exec_delegates_to_builtin_exec_observed";
      "builtin_exec_operation_observed";
      "input_length_observed";
      "last_index_read_observed";
      "original_flags_read_observed";
      "global_flag_computed_observed";
      "sticky_flag_computed_observed";
      "has_indices_flag_computed_observed";
      "non_global_non_sticky_last_index_reset_observed";
      "matcher_read_observed";
      "full_unicode_flag_computed_observed";
      "match_succeeded_initialized_false_observed";
      "input_list_created_observed";
      "input_character_note_observed";
      "input_index_from_last_index_observed";
    ]
  in
  let result_fields =
    match exec_result with
    | None -> []
    | Some _ ->
      [
        "match_state_assertion_observed";
        "match_succeeded_set_true_observed";
        "result_array_created_observed";
        "result_array_length_observed";
        "result_index_property_observed";
        "result_input_property_observed";
        "result_zero_property_observed";
        "groups_property_observed";
        "matched_group_names_list_created_observed";
        "capture_iteration_observed";
        "return_array_observed";
        "search_loop_observed";
        "matcher_invoked_at_input_index_observed";
        "matcher_failure_observed";
        "advance_string_index_observed";
        "success_branch_observed";
        "end_index_read_observed";
        "match_record_created_observed";
        "matched_substring_observed";
      ]
  in
  let group_fields =
    if has_groups then
      [
        "named_groups_branch_observed";
        "groups_object_created_observed";
        "has_groups_true_observed";
        "named_capture_branch_observed";
        "capturing_group_name_read_observed";
        "matched_group_names_duplicate_check_observed";
        "named_capture_else_branch_observed";
        "matched_group_name_appended_observed";
        "named_group_property_created_observed";
        "group_name_appended_observed";
      ]
    else
      [
        "no_groups_branch_observed";
        "groups_undefined_observed";
        "has_groups_false_observed";
        "unnamed_capture_branch_observed";
        "undefined_group_name_appended_observed";
      ]
  in
  let scenario_fields =
    match model_scenario with
    | "regexp_exec_object_dispatch" ->
      [
        "regexp_exec_get_exec_property_observed";
        "regexp_exec_callable_exec_branch_observed";
        "regexp_exec_custom_exec_call_observed";
        "regexp_exec_custom_result_type_guard_observed";
        "regexp_exec_custom_result_return_observed";
      ]
    | "last_index_out_of_bounds_global" ->
      [
        "last_index_greater_than_length_branch_observed";
        "global_or_sticky_oob_reset_branch_observed";
        "last_index_reset_to_zero_observed";
        "return_null_on_oob_observed";
      ]
    | "sticky_failure" ->
      [
        "sticky_failure_branch_observed";
        "sticky_failure_reset_last_index_observed";
        "sticky_failure_return_null_observed";
      ]
    | "unicode_success" ->
      [
        "full_unicode_end_index_conversion_observed";
        "full_unicode_capture_conversion_branch_observed";
        "capture_start_get_string_index_observed";
        "capture_end_get_string_index_observed";
      ]
    | "global_success" ->
      [
        "global_or_sticky_success_branch_observed";
        "last_index_updated_to_end_observed";
      ]
    | "duplicate_named_groups" ->
      [
        "matched_group_names_duplicate_check_observed";
        "duplicate_group_assert_undefined_observed";
        "duplicate_group_undefined_appended_observed";
        "duplicate_group_note_observed";
      ]
    | _ -> []
  in
  {
    observed_model_fields =
      add_many base_fields []
      |> add_many result_fields
      |> add_many group_fields
      |> add_many scenario_fields
      |> List.rev
      |> Array.of_list;
    exec_result;
    input_length;
    last_index_before;
    last_index_after;
    has_groups;
    exec_result_group_names = group_names;
  }

let empty_exec_result_indices_model flags =
  {
    has_indices_flag = flags.has_indices;
    indices_list_initialized = false;
    group_names_list_initialized = false;
    full_match_appended_to_indices = false;
    undefined_capture_appended_to_indices = false;
    has_indices_branch_observed = false;
    indices_array_built = false;
    result_indices_property_observed = false;
    get_match_index_pair_observed = false;
    index_pair_range_valid = false;
    index_pair_start_end_observed = false;
    make_match_indices_array_observed = false;
    indices_array_length = 0;
    indices_array_length_observed = false;
    indices_length_within_array_limit = false;
    group_names_length = 0;
    group_names_length_matches = false;
    group_names_aligned_with_captures = false;
    indices_array_created = false;
    has_groups = false;
    has_groups_branch_observed = false;
    no_groups_branch_observed = false;
    indices_groups_object_created = false;
    indices_groups_undefined_observed = false;
    indices_groups_property_observed = false;
    indices_iteration_observed = false;
    indices_entry_read = false;
    defined_index_entry_observed = false;
    get_match_index_pair_called = false;
    undefined_index_entry_observed = false;
    undefined_index_pair_observed = false;
    indices_numeric_property_observed = false;
    capture_index_entry_observed = false;
    group_name_read = false;
    defined_group_name_observed = false;
    named_groups_object_asserted = false;
    duplicate_group_name_observed = false;
    named_group_property_observed = false;
    indices_array_returned = false;
    exec_result_indices = [||];
    exec_result_group_names = [||];
  }

let inspect_exec_result_indices_model (Compiled (_source, flags, ast)) input =
  match exec_ast_state flags ast input with
  | None -> empty_exec_result_indices_model flags
  | Some (start_index, end_index, state) ->
    let full_match =
      Some
        {
          index_pair_start_index = start_index;
          index_pair_end_index = end_index;
        }
    in
    let capture_indices = Array.map index_pair_of_range state.captures in
    let exec_result_indices =
      Array.init
        (Array.length capture_indices + 1)
        (fun index ->
           if index = 0 then full_match else capture_indices.(index - 1))
    in
    let group_names = capture_names_ast ast in
    let has_groups = array_exists Option.is_some group_names in
    let duplicate_group_name_observed =
      duplicate_group_name_observed group_names
    in
    let has_indices_branch_observed = flags.has_indices in
    let defined_index_entry_observed =
      array_exists Option.is_some exec_result_indices
    in
    let undefined_index_entry_observed =
      array_exists Option.is_none exec_result_indices
    in
    {
      has_indices_flag = flags.has_indices;
      indices_list_initialized = true;
      group_names_list_initialized = true;
      full_match_appended_to_indices = true;
      undefined_capture_appended_to_indices = undefined_index_entry_observed;
      has_indices_branch_observed;
      indices_array_built = has_indices_branch_observed;
      result_indices_property_observed = has_indices_branch_observed;
      get_match_index_pair_observed = defined_index_entry_observed;
      index_pair_range_valid =
        Array.for_all (index_pair_range_valid (String.length input))
          exec_result_indices;
      index_pair_start_end_observed = defined_index_entry_observed;
      make_match_indices_array_observed = has_indices_branch_observed;
      indices_array_length = Array.length exec_result_indices;
      indices_array_length_observed = has_indices_branch_observed;
      indices_length_within_array_limit = Array.length exec_result_indices >= 0;
      group_names_length = Array.length group_names;
      group_names_length_matches =
        Array.length group_names = Array.length exec_result_indices - 1;
      group_names_aligned_with_captures =
        Array.length group_names = Array.length state.captures;
      indices_array_created = has_indices_branch_observed;
      has_groups;
      has_groups_branch_observed = has_groups;
      no_groups_branch_observed = not has_groups;
      indices_groups_object_created = has_groups && has_indices_branch_observed;
      indices_groups_undefined_observed =
        (not has_groups) && has_indices_branch_observed;
      indices_groups_property_observed = has_indices_branch_observed;
      indices_iteration_observed = Array.length exec_result_indices > 0;
      indices_entry_read = Array.length exec_result_indices > 0;
      defined_index_entry_observed;
      get_match_index_pair_called = defined_index_entry_observed;
      undefined_index_entry_observed;
      undefined_index_pair_observed = undefined_index_entry_observed;
      indices_numeric_property_observed = has_indices_branch_observed;
      capture_index_entry_observed = Array.length exec_result_indices > 1;
      group_name_read = has_groups;
      defined_group_name_observed = has_groups;
      named_groups_object_asserted = has_groups && has_indices_branch_observed;
      duplicate_group_name_observed;
      named_group_property_observed = has_groups && has_indices_branch_observed;
      indices_array_returned = has_indices_branch_observed;
      exec_result_indices;
      exec_result_group_names = group_names;
    }

let inspect_exec_result_capture_model (Compiled (_source, flags, ast)) input =
  let capture_count = count_captures_ast ast in
  match exec_ast_state flags ast input with
  | None ->
    {
      capture_slot_count = 0;
      regexp_record_capture_count = capture_count;
      capture_count_matches_regexp_record = capture_count = 0;
      capture_count_within_array_limit = capture_count >= 0;
      undefined_capture_observed = false;
      defined_capture_observed = false;
      capture_start_index_observed = false;
      capture_end_index_observed = false;
      capture_record_observed = false;
      captured_value_observed = false;
      capture_index_list_append_observed = false;
      result_capture_property_observed = false;
      exec_result_captures = [||];
    }
  | Some (_start_index, _end_index, state) ->
    let captures =
      Array.mapi (exec_result_capture_of_range input) state.captures
    in
    let undefined_capture_observed =
      Array.exists (fun capture -> capture.captured_text = None) captures
    in
    let defined_capture_observed =
      Array.exists (fun capture -> capture.captured_text <> None) captures
    in
    {
      capture_slot_count = Array.length state.captures;
      regexp_record_capture_count = capture_count;
      capture_count_matches_regexp_record =
        Array.length state.captures = capture_count;
      capture_count_within_array_limit = capture_count >= 0;
      undefined_capture_observed;
      defined_capture_observed;
      capture_start_index_observed = defined_capture_observed;
      capture_end_index_observed = defined_capture_observed;
      capture_record_observed = defined_capture_observed;
      captured_value_observed = defined_capture_observed;
      capture_index_list_append_observed = defined_capture_observed;
      result_capture_property_observed = capture_count > 0;
      exec_result_captures = captures;
    }

let unsupported_match_engine_message operation construct =
  operation ^ ": match semantics are not implemented for " ^ construct

let instance regexp = { regexp; last_index = 0 }

let last_index instance = instance.last_index

let set_last_index instance last_index =
  if last_index < 0 then invalid_arg "Ecma_regex.set_last_index: negative index";
  instance.last_index <- last_index

let exec (Compiled (_source, flags, ast)) input =
  try exec_ast flags ast input with
  | Unsupported_match_engine construct ->
    invalid_arg (unsupported_match_engine_message "Ecma_regex.exec" construct)

let search (Compiled (_source, flags, ast)) input =
  try
    match exec_ast flags ast input with
    | Some _ -> true
    | None -> false
  with
  | Unsupported_match_engine construct ->
    invalid_arg (unsupported_match_engine_message "Ecma_regex.search" construct)

let search_index (Compiled (_source, flags, ast)) input =
  try
    match exec_ast flags ast input with
    | Some result -> result.start_index
    | None -> -1
  with
  | Unsupported_match_engine construct ->
    invalid_arg
      (unsupported_match_engine_message "Ecma_regex.search_index" construct)

let exec_js (Compiled (_source, flags, ast)) (Js_string input) =
  try
    match exec_ast_state flags ast input with
    | None -> None
    | Some (start_index, end_index, state) ->
      Some (js_match_result_of_state input ast start_index end_index state)
  with
  | Unsupported_match_engine construct ->
    invalid_arg (unsupported_match_engine_message "Ecma_regex.exec_js" construct)

let search_js (Compiled (_source, flags, ast)) (Js_string input) =
  try
    match exec_ast flags ast input with
    | Some _ -> true
    | None -> false
  with
  | Unsupported_match_engine construct ->
    invalid_arg (unsupported_match_engine_message "Ecma_regex.search_js" construct)

let search_index_js (Compiled (_source, flags, ast)) (Js_string input) =
  try
    match exec_ast flags ast input with
    | Some result -> result.start_index
    | None -> -1
  with
  | Unsupported_match_engine construct ->
    invalid_arg
      (unsupported_match_engine_message "Ecma_regex.search_index_js" construct)

let exec_instance_state operation
    ({ regexp = Compiled (_source, flags, ast); last_index } as instance)
    input =
  try
    let uses_last_index = flags.global || flags.sticky in
    let input_length = utf16_code_unit_length_of_utf8 input in
    let start_index = if uses_last_index then last_index else 0 in
    if start_index > input_length then begin
      if uses_last_index then instance.last_index <- 0;
      None
    end
    else
      let start_byte_index =
        utf8_byte_index_of_utf16_code_unit_index input start_index
      in
      match exec_ast_state_from_byte_index flags ast input start_byte_index with
      | None ->
        if uses_last_index then instance.last_index <- 0;
        None
      | Some (start_byte, end_byte, state) ->
        let result = match_result_of_byte_range input start_byte end_byte in
        if uses_last_index then instance.last_index <- result.end_index;
        Some (ast, start_byte, end_byte, state)
  with
  | Unsupported_match_engine construct ->
    invalid_arg (unsupported_match_engine_message operation construct)

let exec_instance instance input =
  match exec_instance_state "Ecma_regex.exec_instance" instance input with
  | None -> None
  | Some (_ast, start_index, end_index, _state) ->
    Some (match_result_of_byte_range input start_index end_index)

let search_instance_index instance input =
  let previous_last_index = instance.last_index in
  instance.last_index <- 0;
  try
    let result =
      match exec_instance instance input with
      | None -> -1
      | Some result -> result.start_index
    in
    instance.last_index <- previous_last_index;
    result
  with exn ->
    instance.last_index <- previous_last_index;
    raise exn

let exec_instance_js instance (Js_string input) =
  match exec_instance_state "Ecma_regex.exec_instance_js" instance input with
  | None -> None
  | Some (ast, start_index, end_index, state) ->
    Some (js_match_result_of_state input ast start_index end_index state)

let search_instance_index_js instance input =
  let previous_last_index = instance.last_index in
  instance.last_index <- 0;
  try
    let result =
      match exec_instance_js instance input with
      | None -> -1
      | Some result -> result.js_start_index
    in
    instance.last_index <- previous_last_index;
    result
  with exn ->
    instance.last_index <- previous_last_index;
    raise exn

let match_instance ({ regexp = Compiled (_source, flags, _); _ } as instance)
    input =
  if not flags.global then
    match exec_instance instance input with
    | None -> None
    | Some result -> Some [ result ]
  else begin
    instance.last_index <- 0;
    let rec loop matches =
      match exec_instance instance input with
      | None ->
        if matches = [] then None else Some (List.rev matches)
      | Some result ->
        if result.matched_text = "" then begin
          let this_index = last_index instance in
          let next_index =
            advance_string_index input this_index (has_unicode_semantics flags)
          in
          set_last_index instance next_index
        end;
        loop (result :: matches)
    in
    loop []
  end

let match_ regexp input = match_instance (instance regexp) input

let match_instance_js
    ({ regexp = Compiled (_source, flags, _); _ } as instance)
    ((Js_string input) as js_input) =
  if not flags.global then
    match exec_instance_js instance js_input with
    | None -> None
    | Some result -> Some [ result ]
  else begin
    instance.last_index <- 0;
    let rec loop matches =
      match exec_instance_js instance js_input with
      | None ->
        if matches = [] then None else Some (List.rev matches)
      | Some result ->
        if js_string_to_utf16_code_units result.js_matched_text = [] then begin
          let this_index = last_index instance in
          let next_index =
            advance_string_index input this_index (has_unicode_semantics flags)
          in
          set_last_index instance next_index
        end;
        loop (result :: matches)
    in
    loop []
  end

let match_js regexp input = match_instance_js (instance regexp) input

let iter_matches ({ regexp = Compiled (_source, flags, _); _ } as instance) input =
  {
    iterating_regexp = instance;
    iterated_string = input;
    iter_global = flags.global;
    iter_unicode = has_unicode_semantics flags;
    iter_done = false;
  }

let next_match iterator =
  if iterator.iter_done then None
  else
    match exec_instance iterator.iterating_regexp iterator.iterated_string with
    | None ->
      iterator.iter_done <- true;
      None
    | Some result ->
      if not iterator.iter_global then iterator.iter_done <- true
      else if result.matched_text = "" then begin
        let this_index = last_index iterator.iterating_regexp in
        let next_index =
          advance_string_index iterator.iterated_string this_index
            iterator.iter_unicode
        in
        set_last_index iterator.iterating_regexp next_index
      end;
      Some result

let iter_matches_js ({ regexp = Compiled (_source, flags, _); _ } as instance)
    input =
  {
    js_iterating_regexp = instance;
    js_iterated_string = input;
    js_iter_global = flags.global;
    js_iter_unicode = has_unicode_semantics flags;
    js_iter_done = false;
  }

let next_match_js iterator =
  if iterator.js_iter_done then None
  else
    match exec_instance_js iterator.js_iterating_regexp iterator.js_iterated_string with
    | None ->
      iterator.js_iter_done <- true;
      None
    | Some result ->
      if not iterator.js_iter_global then iterator.js_iter_done <- true
      else if js_string_to_utf16_code_units result.js_matched_text = [] then begin
        let Js_string input = iterator.js_iterated_string in
        let this_index = last_index iterator.js_iterating_regexp in
        let next_index =
          advance_string_index input this_index iterator.js_iter_unicode
        in
        set_last_index iterator.js_iterating_regexp next_index
      end;
      Some result

let match_all_instance instance input =
  let clone =
    { regexp = instance.regexp; last_index = instance.last_index }
  in
  let iterator = iter_matches clone input in
  let rec loop matches =
    match next_match iterator with
    | None -> List.rev matches
    | Some result -> loop (result :: matches)
  in
  loop []

let match_all regexp input = match_all_instance (instance regexp) input

let match_all_instance_js instance input =
  let clone =
    { regexp = instance.regexp; last_index = instance.last_index }
  in
  let iterator = iter_matches_js clone input in
  let rec loop matches =
    match next_match_js iterator with
    | None -> List.rev matches
    | Some result -> loop (result :: matches)
  in
  loop []

let match_all_js regexp input = match_all_instance_js (instance regexp) input

let split_limit operation = function
  | None -> max_int
  | Some limit when limit < 0 ->
    invalid_arg (operation ^ ": negative limit")
  | Some limit -> limit

let split_instance_parts operation make_text make_capture ?limit
    ({ regexp = Compiled (source, flags, ast); _ }) input =
  let limit = split_limit operation limit in
  if limit = 0 then []
  else
    let unicode_matching = has_unicode_semantics flags in
    let splitter =
      {
        regexp = Compiled (source, { flags with sticky = true }, ast);
        last_index = 0;
      }
    in
    let size = utf16_code_unit_length_of_utf8 input in
    let text_part start_index end_index =
      make_text (utf8_substring_by_utf16_code_units input start_index end_index)
    in
    let capture_part range = make_capture (text_of_capture_range input range) in
    let append part acc length =
      let length = length + 1 in
      (part :: acc, length, length = limit)
    in
    let rec append_captures captures index acc length =
      if index >= Array.length captures then `Continue (acc, length)
      else
        let acc, length, done_ = append (capture_part captures.(index)) acc length in
        if done_ then `Done acc
        else append_captures captures (index + 1) acc length
    in
    let rec loop p q acc length =
      if q >= size then
        let acc, _length, _done = append (text_part p size) acc length in
        List.rev acc
      else begin
        splitter.last_index <- q;
        match exec_instance_state operation splitter input with
        | None ->
          loop p (advance_string_index input q unicode_matching) acc length
        | Some (_ast, _start_index, _end_index, state) ->
          let e = min (last_index splitter) size in
          if e = p then
            loop p (advance_string_index input q unicode_matching) acc length
          else
            let acc, length, done_ = append (text_part p q) acc length in
            if done_ then List.rev acc
            else
              let p = e in
              match append_captures state.captures 0 acc length with
              | `Done acc -> List.rev acc
              | `Continue (acc, length) -> loop p p acc length
      end
    in
    if size = 0 then begin
      splitter.last_index <- 0;
      match exec_instance_state operation splitter input with
      | Some _ -> []
      | None -> [ text_part 0 0 ]
    end
    else loop 0 0 [] 0

let split_instance ?limit instance input =
  split_instance_parts
    "Ecma_regex.split_instance"
    (fun text -> Split_text text)
    (fun capture -> Split_capture capture)
    ?limit
    instance
    input

let split ?limit regexp input =
  split_instance ?limit (instance regexp) input

let split_instance_js ?limit instance (Js_string input) =
  split_instance_parts
    "Ecma_regex.split_instance_js"
    (fun text -> Js_split_text (Js_string text))
    (fun capture ->
       Js_split_capture (Option.map (fun text -> Js_string text) capture))
    ?limit
    instance
    input

let split_js ?limit regexp input =
  split_instance_js ?limit (instance regexp) input

let regexp_with_global = function
  | Compiled (source, flags, ast) ->
    Compiled (source, { flags with global = true }, ast)

let regexp_has_global = function
  | Compiled (_source, flags, _ast) -> flags.global

let regexp_unicode_matching = function
  | Compiled (_source, flags, _ast) -> has_unicode_semantics flags

let next_storage_index value index =
  match utf8_decode_next value index with
  | Some (next_index, _) when next_index > index -> next_index
  | _ -> min (String.length value) (index + 1)

let named_capture_lookup input ast captures name =
  let names = capture_names_ast ast in
  let rec loop index =
    if index >= Array.length names then None
    else
      match names.(index) with
      | Some candidate when String.equal candidate name ->
        text_of_capture_range input captures.(index)
      | _ -> loop (index + 1)
  in
  loop 0

let has_named_captures ast =
  let names = capture_names_ast ast in
  array_exists Option.is_some names

let find_gt value start =
  let length = String.length value in
  let rec loop index =
    if index >= length then None
    else if value.[index] = '>' then Some index
    else loop (next_storage_index value index)
  in
  loop start

let digit_value value index =
  if index >= String.length value then None
  else
    match value.[index] with
    | '0' .. '9' as ch -> Some (Char.code ch - Char.code '0')
    | _ -> None

let add_substring buffer value start_index end_index =
  if end_index > start_index then
    Buffer.add_substring buffer value start_index (end_index - start_index)

let add_capture_or_empty buffer input captures index =
  match text_of_capture_range input captures.(index) with
  | None -> ()
  | Some text -> Buffer.add_string buffer text

let add_get_substitution buffer input ast captures matched start_byte end_byte
    replacement =
  let replacement_length = String.length replacement in
  let capture_count = Array.length captures in
  let named_captures_defined = has_named_captures ast in
  let rec loop index =
    if index >= replacement_length then ()
    else if replacement.[index] <> '$' then begin
      let next_index = next_storage_index replacement index in
      add_substring buffer replacement index next_index;
      loop next_index
    end
    else if index + 1 >= replacement_length then begin
      Buffer.add_char buffer '$';
      loop (index + 1)
    end
    else
      match replacement.[index + 1] with
      | '$' ->
        Buffer.add_char buffer '$';
        loop (index + 2)
      | '`' ->
        add_substring buffer input 0 start_byte;
        loop (index + 2)
      | '&' ->
        Buffer.add_string buffer matched;
        loop (index + 2)
      | '\'' ->
        add_substring buffer input end_byte (String.length input);
        loop (index + 2)
      | '<' ->
        (match find_gt replacement (index + 2) with
         | None ->
           Buffer.add_string buffer "$<";
           loop (index + 2)
         | Some _gt_index when not named_captures_defined ->
           Buffer.add_string buffer "$<";
           loop (index + 2)
         | Some gt_index ->
           let name =
             String.sub replacement (index + 2) (gt_index - index - 2)
           in
           (match named_capture_lookup input ast captures name with
            | None -> ()
            | Some text -> Buffer.add_string buffer text);
           loop (gt_index + 1))
      | '0' .. '9' ->
        let first_digit =
          match digit_value replacement (index + 1) with
          | Some digit -> digit
          | None -> assert false
        in
        let digit_count, capture_index =
          match digit_value replacement (index + 2) with
          | Some second_digit ->
            let two_digit_index = (first_digit * 10) + second_digit in
            if two_digit_index > capture_count then (1, first_digit)
            else (2, two_digit_index)
          | None -> (1, first_digit)
        in
        if capture_index >= 1 && capture_index <= capture_count then
          add_capture_or_empty buffer input captures (capture_index - 1)
        else
          add_substring buffer replacement index (index + 1 + digit_count);
        loop (index + 1 + digit_count)
      | _ ->
        Buffer.add_char buffer '$';
        loop (index + 1)
  in
  loop 0

let replace_instance_storage operation ~replacement
    ({ regexp = Compiled (_source, flags, _ast) as regexp; _ } as instance)
    input =
  if flags.global then instance.last_index <- 0;
  let unicode_matching = regexp_unicode_matching regexp in
  let rec collect acc =
    match exec_instance_state operation instance input with
    | None -> List.rev acc
    | Some (ast, start_byte, end_byte, state) ->
      let matched = String.sub input start_byte (end_byte - start_byte) in
      let acc = (ast, start_byte, end_byte, state, matched) :: acc in
      if not (regexp_has_global regexp) then List.rev acc
      else begin
        if start_byte = end_byte then begin
          let this_index = last_index instance in
          let next_index = advance_string_index input this_index unicode_matching in
          set_last_index instance next_index
        end;
        collect acc
      end
  in
  match collect [] with
  | [] -> input
  | matches ->
    let buffer = Buffer.create (String.length input + String.length replacement) in
    let rec append_matches next_source_byte = function
      | [] ->
        add_substring buffer input next_source_byte (String.length input)
      | (ast, start_byte, end_byte, state, matched) :: rest ->
        if start_byte >= next_source_byte then begin
          add_substring buffer input next_source_byte start_byte;
          add_get_substitution buffer input ast state.captures matched start_byte
            end_byte replacement;
          append_matches end_byte rest
        end
        else append_matches next_source_byte rest
    in
    append_matches 0 matches;
    Buffer.contents buffer

let replace_instance ~replacement instance input =
  replace_instance_storage "Ecma_regex.replace_instance" ~replacement instance input

let replace ~replacement regexp input =
  replace_instance ~replacement (instance regexp) input

let replace_all_instance ~replacement instance input =
  let replace_all_instance =
    {
      regexp = regexp_with_global instance.regexp;
      last_index = 0;
    }
  in
  replace_instance_storage "Ecma_regex.replace_all_instance" ~replacement
    replace_all_instance input

let replace_all ~replacement regexp input =
  replace_all_instance ~replacement (instance regexp) input

let replace_instance_js ~replacement instance (Js_string input) =
  let Js_string replacement = replacement in
  Js_string
    (replace_instance_storage "Ecma_regex.replace_instance_js" ~replacement
       instance input)

let replace_js ~replacement regexp input =
  replace_instance_js ~replacement (instance regexp) input

let replace_all_instance_js ~replacement instance (Js_string input) =
  let Js_string replacement = replacement in
  let replace_all_instance =
    {
      regexp = regexp_with_global instance.regexp;
      last_index = 0;
    }
  in
  Js_string
    (replace_instance_storage "Ecma_regex.replace_all_instance_js" ~replacement
       replace_all_instance input)

let replace_all_js ~replacement regexp input =
  replace_all_instance_js ~replacement (instance regexp) input
