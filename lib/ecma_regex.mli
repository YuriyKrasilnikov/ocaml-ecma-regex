(** ECMAScript regular expressions.

    This module exposes ECMAScript [RegExp] syntax and matching semantics
    through explicit OCaml functions. JavaScript object dispatch, constructors,
    prototype mutation, and dynamic method lookup are outside this public
    surface. *)

type t
(** A compiled ECMAScript regular expression. *)

type instance
(** A mutable ECMAScript RegExp instance carrying [lastIndex] state. *)

type match_iterator
(** An explicit RegExp string iterator over one input string. *)

type js_string
(** An explicit ECMAScript String value represented as UTF-16 code units. *)

type js_capture = {
  js_capture_index : int;
  js_capture_start_index : int option;
  js_capture_end_index : int option;
  js_capture_text : js_string option;
}
(** A numbered capture in a successful explicit ECMAScript String match.
    [js_capture_index] is the one-based capture ordinal from the regexp source.
    Undefined captures have no text and no start/end indices. *)

type js_named_capture = {
  js_named_capture_name : string;
  js_named_capture : js_capture;
}
(** A named capture in a successful explicit ECMAScript String match. *)

type js_match_result = {
  js_start_index : int;
  js_end_index : int;
  js_matched_text : js_string;
  js_captures : js_capture list;
  js_named_captures : js_named_capture list;
}
(** A successful match result over an explicit ECMAScript String value. *)

(** One element returned by explicit RegExp split semantics. Text elements are
    substrings that remain after removing matches. Capture elements are numbered
    captures inserted after a separator match; [None] represents an unmatched
    ECMAScript capture, i.e. JavaScript [undefined]. *)
type split_part = Split_text of string | Split_capture of string option

(** One split element over an explicit ECMAScript String. *)
type js_split_part =
  | Js_split_text of js_string
  | Js_split_capture of js_string option

type js_match_iterator
(** An explicit RegExp string iterator over an explicit ECMAScript String. *)

type syntax_error = string
(** A compile-time syntax error rendered as a diagnostic string. *)

type flags
(** ECMAScript regular-expression flags. *)

type regexp_literal = private {
  pattern_text : string;
  flag_text : string;
  flags : flags;
}
(** A parsed ECMAScript regular-expression literal. *)

type match_result = {
  start_index : int;
  end_index : int;
  matched_text : string;
}
(** A successful regular-expression match result over an OCaml UTF-8 string.
    Indices are ECMAScript UTF-16 code-unit indices. *)

val flags :
  ?has_indices:bool ->
  ?global:bool ->
  ?ignore_case:bool ->
  ?multiline:bool ->
  ?dot_all:bool ->
  ?unicode:bool ->
  ?unicode_sets:bool ->
  ?sticky:bool ->
  unit ->
  flags
(** [flags ?has_indices ?global ?ignore_case ?multiline ?dot_all ?unicode
     ?unicode_sets ?sticky ()] constructs an explicit flag set. *)

val flags_of_string : string -> (flags, syntax_error) result
(** [flags_of_string s] parses ECMAScript flags from [s]. Duplicate or unknown
    flags are rejected. *)

val regexp_literal_of_string : string -> (regexp_literal, syntax_error) result
(** [regexp_literal_of_string s] parses a complete ECMAScript regular-expression
    literal source such as ["/a/g"]. The returned [flag_text] is the exact
    source text recognized as [RegularExpressionFlags]. *)

val compile : ?flags:flags -> string -> (t, syntax_error) result
(** [compile ?flags pattern] compiles [pattern] using ECMAScript
    regular-expression syntax. Patterns are not implicitly anchored. *)

val exec : t -> string -> match_result option
(** [exec re s] returns the first full-match result when [re] matches somewhere
    in [s]. Use [exec_js] when capture ranges and raw ECMAScript String slices
    are required. *)

val search : t -> string -> bool
(** [search re s] returns [true] when [re] matches somewhere in [s]. *)

val search_index : t -> string -> int
(** [search_index re s] returns the UTF-16 code-unit start index of the first
    match, or [-1] when [re] does not match [s]. This is the explicit OCaml
    adapter shape for ECMAScript search semantics without JavaScript object
    protocol. *)

val match_ : t -> string -> match_result list option
(** [match_ re s] returns ECMAScript match adapter results over [s]. For
    non-global regexps this is the first [exec] result, or [None] when there is
    no match. For global regexps this is the full list of matched spans, or
    [None] when there are no matches. *)

val match_all : t -> string -> match_result list
(** [match_all re s] returns all ECMAScript matchAll adapter results over [s].
    Unlike [match_], absence of matches is the empty list because ECMAScript
    [matchAll] returns an iterator rather than [null]. Non-global regexps yield
    at most one match; global regexps iterate with [AdvanceStringIndex] after
    empty matches. *)

val split : ?limit:int -> t -> string -> split_part list
(** [split ?limit re s] returns ECMAScript RegExp split adapter results over
    [s]. The adapter models RegExp.prototype[@@split] over an explicit compiled
    regexp: it uses a fresh sticky splitter, does not mutate [re] or a caller's
    instance state, applies [limit], advances after empty matches with
    [AdvanceStringIndex], and inserts numbered captures. *)

val replace : replacement:string -> t -> string -> string
(** [replace ~replacement re s] returns ECMAScript RegExp replacement adapter
    results over [s]. The adapter models RegExp.prototype[@@replace] over an
    explicit compiled regexp and a string replacement template: non-global
    regexps replace the first match, global regexps replace every match, empty
    global matches advance with [AdvanceStringIndex], and [$] replacement
    patterns are interpreted with numbered and named captures. *)

val replace_all : replacement:string -> t -> string -> string
(** [replace_all ~replacement re s] replaces every match in [s] using the same
    replacement-template semantics as [replace]. This is an explicit OCaml
    helper over the regexp engine; it does not model JavaScript object dispatch
    for [String.prototype.replaceAll]. *)

val escape : string -> string
(** [escape s] returns ECMA-262 [RegExp.escape] pattern text for matching [s]
    literally. *)

val js_string_of_utf8 : string -> js_string
(** [js_string_of_utf8 s] constructs an ECMAScript String from UTF-8 text. *)

val js_string_of_utf16_code_units : int list -> (js_string, syntax_error) result
(** [js_string_of_utf16_code_units units] constructs an ECMAScript String from
    raw UTF-16 code units. Values outside [0x0000, 0xFFFF] are rejected. *)

val js_string_to_utf16_code_units : js_string -> int list
(** [js_string_to_utf16_code_units s] exposes [s]'s raw UTF-16 code units. *)

val exec_js : t -> js_string -> js_match_result option
(** [exec_js re s] executes [re] against explicit ECMAScript String [s],
    exposing full-match and capture ranges as UTF-16 code-unit indices. *)

val search_js : t -> js_string -> bool
(** [search_js re s] returns [true] when [re] matches explicit ECMAScript String
    [s]. *)

val search_index_js : t -> js_string -> int
(** [search_index_js re s] is [search_index] over explicit ECMAScript String
    [s]. *)

val match_js : t -> js_string -> js_match_result list option
(** [match_js re s] is [match_] over explicit ECMAScript String [s], exposing
    UTF-16 indices, raw matched text, and capture data. *)

val match_all_js : t -> js_string -> js_match_result list
(** [match_all_js re s] is [match_all] over explicit ECMAScript String [s],
    exposing UTF-16 indices, raw matched text, and capture data. *)

val split_js : ?limit:int -> t -> js_string -> js_split_part list
(** [split_js ?limit re s] is [split] over explicit ECMAScript String [s],
    preserving raw UTF-16 slices in text and capture elements. *)

val replace_js : replacement:js_string -> t -> js_string -> js_string
(** [replace_js ~replacement re s] is [replace] over explicit ECMAScript String
    values, preserving raw UTF-16 replacement and input slices. *)

val replace_all_js : replacement:js_string -> t -> js_string -> js_string
(** [replace_all_js ~replacement re s] is [replace_all] over explicit ECMAScript
    String values. *)

val escape_js : js_string -> js_string
(** [escape_js s] is [escape] over explicit ECMAScript String [s], preserving
    raw UTF-16 semantics for valid surrogate pairs and lone surrogates. *)

val instance : t -> instance
(** [instance re] creates an explicit mutable RegExp instance for APIs that need
    ECMAScript [lastIndex] state. *)

val last_index : instance -> int
(** [last_index i] returns [i]'s current ECMAScript UTF-16 code-unit
    [lastIndex]. *)

val set_last_index : instance -> int -> unit
(** [set_last_index i n] sets [i]'s ECMAScript UTF-16 code-unit [lastIndex].
    Negative indices are rejected. *)

val exec_instance : instance -> string -> match_result option
(** [exec_instance i s] executes [i]'s regexp against [s] using and updating
    explicit [lastIndex] state for global or sticky regexps. Stateless regexps
    ignore [lastIndex] and leave it unchanged. *)

val search_instance_index : instance -> string -> int
(** [search_instance_index i s] executes search semantics through [i],
    temporarily using [lastIndex = 0] and restoring [i]'s previous [lastIndex]
    before returning. The result is the UTF-16 code-unit start index, or [-1] on
    no match. *)

val match_instance : instance -> string -> match_result list option
(** [match_instance i s] executes ECMAScript match adapter semantics through
    [i]. Global regexps start at [lastIndex = 0], collect all full matches, and
    leave [lastIndex] at the value produced by the terminal [exec] attempt.
    Non-global regexps delegate to one [exec_instance] call. *)

val match_all_instance : instance -> string -> match_result list
(** [match_all_instance i s] executes ECMAScript matchAll adapter semantics
    through a cloned matcher state initialized from [i]'s current [lastIndex].
    The original instance is not mutated. *)

val split_instance : ?limit:int -> instance -> string -> split_part list
(** [split_instance ?limit i s] executes RegExp split adapter semantics through
    [i]'s regexp using a fresh sticky splitter. The original instance and its
    [lastIndex] are not mutated. *)

val replace_instance : replacement:string -> instance -> string -> string
(** [replace_instance ~replacement i s] executes RegExp replacement semantics
    through [i]. Global regexps reset [lastIndex] before collecting matches;
    non-global regexps delegate to one [exec_instance] call. *)

val replace_all_instance : replacement:string -> instance -> string -> string
(** [replace_all_instance ~replacement i s] replaces all matches through a
    cloned global matcher and leaves [i]'s [lastIndex] unchanged. *)

val exec_instance_js : instance -> js_string -> js_match_result option
(** [exec_instance_js i s] is [exec_instance] over explicit ECMAScript String
    [s]. *)

val search_instance_index_js : instance -> js_string -> int
(** [search_instance_index_js i s] is [search_instance_index] over explicit
    ECMAScript String [s]. *)

val match_instance_js : instance -> js_string -> js_match_result list option
(** [match_instance_js i s] is [match_instance] over explicit ECMAScript String
    [s]. *)

val match_all_instance_js : instance -> js_string -> js_match_result list
(** [match_all_instance_js i s] is [match_all_instance] over explicit ECMAScript
    String [s]. *)

val split_instance_js :
  ?limit:int -> instance -> js_string -> js_split_part list
(** [split_instance_js ?limit i s] is [split_instance] over explicit ECMAScript
    String [s]. *)

val replace_instance_js :
  replacement:js_string -> instance -> js_string -> js_string
(** [replace_instance_js ~replacement i s] is [replace_instance] over explicit
    ECMAScript String values. *)

val replace_all_instance_js :
  replacement:js_string -> instance -> js_string -> js_string
(** [replace_all_instance_js ~replacement i s] is [replace_all_instance] over
    explicit ECMAScript String values. *)

val iter_matches : instance -> string -> match_iterator
(** [iter_matches i s] creates an explicit iterator over [s] using [i]'s mutable
    [lastIndex] state. Global iterators advance [lastIndex] after empty matches
    using ECMAScript [AdvanceStringIndex] rules. *)

val next_match : match_iterator -> match_result option
(** [next_match it] returns the next iterator match, or [None] after exhaustion.
*)

val iter_matches_js : instance -> js_string -> js_match_iterator
(** [iter_matches_js i s] creates an explicit iterator over explicit ECMAScript
    String [s]. *)

val next_match_js : js_match_iterator -> js_match_result option
(** [next_match_js it] returns the next explicit ECMAScript String iterator
    match, or [None] after exhaustion. *)
