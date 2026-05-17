#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import read_tsv


DETAIL_NAME = "ecma262-regexp-product-surface-matrix.tsv"
SUMMARY_NAME = "ecma262-regexp-product-surface-matrix.summary"

ALLOWED_DECISIONS = {
    "core_library_requirement",
    "ocaml_adapter_requirement",
    "test_adapter_only_requirement",
    "non_applicable_with_reason",
    "deferred_with_reason",
}

POLICIES = {
    "22.1.3.13": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "match_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.match_",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_match_adapter.ml",
        "decision_reason": "String.prototype.match rows define user-visible match semantics that can be exposed as an explicit OCaml match/exec adapter without JS object protocol.",
    },
    "22.1.3.14": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "match_all_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.match_all",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_match_all_adapter.ml",
        "decision_reason": "String.prototype.matchAll rows define repeated match semantics; the OCaml surface should expose explicit match-all behavior, not JS iterator objects.",
    },
    "22.1.3.19": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "replace_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.replace",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_replace_adapter.ml",
        "decision_reason": "String.prototype.replace rows define replacement semantics that are meaningful as an explicit OCaml adapter over the regex engine.",
    },
    "22.1.3.19.1": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "replace_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.replace",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_replace_adapter.ml",
        "decision_reason": "GetSubstitution is the core substitution algorithm behind replacement and must be tested with the OCaml replace adapter.",
    },
    "22.1.3.20": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "replace_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.replace_all",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_replace_adapter.ml",
        "decision_reason": "String.prototype.replaceAll rows define full-input replacement semantics that are meaningful as an explicit OCaml adapter.",
    },
    "22.1.3.21": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "search_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.search_index",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_search_adapter.ml",
        "decision_reason": "String.prototype.search semantic rows map to the explicit index-returning Ecma_regex.search_index adapter without JavaScript object dispatch.",
    },
    "22.1.3.23": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "split_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.split",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_split_adapter.ml",
        "decision_reason": "String.prototype.split rows define split semantics that are meaningful as an explicit OCaml adapter over the regex engine.",
    },
    "22.2.3.2": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "js_constructor_or_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "RegExpAlloc is JavaScript object allocation and internal-slot setup; the OCaml library exposes compiled values directly.",
    },
    "22.2.4": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "js_constructor_or_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "The RegExp constructor object is a JavaScript object model feature, not an OCaml library surface.",
    },
    "22.2.4.1": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "js_constructor_or_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "RegExp(pattern, flags) specifies JavaScript constructor dispatch, coercion, NewTarget, and object reuse; OCaml compile/flags cover syntax through separate core rows.",
    },
    "22.2.5": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "js_constructor_or_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "RegExp constructor properties are JavaScript object properties and do not define the OCaml regex engine surface.",
    },
    "22.2.5.1": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "regexp_escape_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.escape",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_escape_adapter.ml",
        "decision_reason": "RegExp.escape is a pure user-facing transformation and should be exposed as an explicit OCaml adapter.",
    },
    "22.2.5.1.1": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "regexp_escape_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.escape",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_escape_adapter.ml",
        "decision_reason": "EncodeForRegExpEscape is the pure algorithm behind RegExp.escape and must be covered through the OCaml escape adapter.",
    },
    "22.2.5.2": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "js_constructor_or_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "RegExp.prototype as a JavaScript prototype object is not an OCaml public API requirement.",
    },
    "22.2.5.3": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "js_constructor_or_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "Symbol.species behavior belongs to JavaScript constructor/prototype integration and has no OCaml library analogue.",
    },
    "22.2.6": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "js_constructor_or_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "The RegExp prototype object container is JavaScript object model structure, not a direct OCaml requirement.",
    },
    "22.2.6.8": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "match_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.match_",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_match_adapter.ml",
        "decision_reason": "RegExp.prototype[@@match] rows define match behavior that should be represented by explicit OCaml match/exec adapters.",
    },
    "22.2.6.9": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "match_all_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.match_all",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_match_all_adapter.ml",
        "decision_reason": "RegExp.prototype[@@matchAll] rows define repeated match behavior; OCaml should expose explicit match-all semantics without JS iterator object identity.",
    },
    "22.2.6.11": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "replace_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.replace",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_replace_adapter.ml",
        "decision_reason": "RegExp.prototype[@@replace] rows define replacement behavior that is meaningful as an explicit OCaml replace adapter.",
    },
    "22.2.6.12": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "search_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.search_index",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_search_adapter.ml",
        "decision_reason": "RegExp.prototype[@@search] semantic rows map to the explicit index-returning Ecma_regex.search_index adapter, with lastIndex preservation covered by the instance variant.",
    },
    "22.2.6.13": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "regexp_source_rendering",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "RegExp.prototype.source is JavaScript property rendering of internal source text; it is not required for core OCaml matching semantics.",
    },
    "22.2.6.14": {
        "surface_decision": "ocaml_adapter_requirement",
        "surface_area": "split_adapter",
        "public_api_status": "current_public_api",
        "ocaml_artifact": "Ecma_regex.split",
        "coverage_action": "add_ocaml_adapter_tests",
        "next_test_artifact": "test/test_ecma262_split_adapter.ml",
        "decision_reason": "RegExp.prototype[@@split] rows define split behavior that is meaningful as an explicit OCaml split adapter.",
    },
    "22.2.6.17": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "regexp_source_rendering",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "RegExp.prototype.toString is JavaScript object stringification, not a required OCaml regex engine behavior.",
    },
    "22.2.9": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "regexp_string_iterator_object",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "RegExp String Iterator object structure is JavaScript iterator object protocol; OCaml match_all can expose iteration without JS object identity.",
    },
    "22.2.9.1": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "regexp_string_iterator_object",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "CreateRegExpStringIterator creates JavaScript iterator objects; OCaml match_all should test semantic results separately from JS object creation.",
    },
    "22.2.9.2": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "regexp_string_iterator_object",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "The RegExpStringIteratorPrototype object is JavaScript prototype structure, not an OCaml library surface.",
    },
    "22.2.9.2.1": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "regexp_string_iterator_object",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "Iterator .next object protocol is JavaScript runtime behavior; OCaml match_all should cover yielded match semantics without JS iterator records.",
    },
    "22.2.9.3": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "regexp_string_iterator_object",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "RegExp String Iterator instance properties are JavaScript object details and do not define OCaml regex semantics.",
    },
    "7.2.6": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "js_constructor_or_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "IsRegExp is a JavaScript object/protocol brand check and has no direct OCaml equivalent.",
    },
    "B.2.4.1": {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "annex_b_mutating_compile",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": "Annex B RegExp.prototype.compile is legacy mutating JavaScript API behavior; the OCaml surface must use explicit compile to create a new value.",
    },
}

SEARCH_NON_OCAML_ROWS = {
    "ecma262-22.1.3.21-0003": "RequireObjectCoercible rejects JavaScript null/undefined receivers; OCaml string arguments are statically non-null.",
    "ecma262-22.1.3.21-0004": "The Object branch is JavaScript dynamic-dispatch setup; the OCaml adapter takes an explicit compiled regexp.",
    "ecma262-22.1.3.21-0005": "GetMethod(regexp, @@search) is JavaScript method lookup and has no OCaml adapter equivalent.",
    "ecma262-22.1.3.21-0006": "The custom @@search branch is JavaScript object protocol; OCaml exposes explicit functions rather than user-provided method properties.",
    "ecma262-22.1.3.21-0007": "Calling a custom searcher is JavaScript dynamic dispatch and is not an OCaml regex-library surface.",
    "ecma262-22.1.3.21-0009": "RegExpCreate from an arbitrary JavaScript argument is constructor/coercion behavior; OCaml callers compile regexps explicitly before search.",
    "ecma262-22.2.6.12-0003": "The non-object receiver TypeError branch is JavaScript runtime type checking; OCaml enforces regexp receiver types statically.",
    "ecma262-22.2.6.12-0014": "The function name property is JavaScript function-object metadata, not OCaml regex search semantics.",
}

MATCH_NON_OCAML_ROWS = {
    "ecma262-22.1.3.13-0003": "RequireObjectCoercible rejects JavaScript null/undefined receivers; OCaml string arguments are statically non-null.",
    "ecma262-22.1.3.13-0004": "The Object branch is JavaScript dynamic-dispatch setup; the OCaml match adapter takes an explicit compiled regexp.",
    "ecma262-22.1.3.13-0005": "GetMethod(regexp, @@match) is JavaScript method lookup and has no OCaml adapter equivalent.",
    "ecma262-22.1.3.13-0006": "The custom @@match branch is JavaScript object protocol; OCaml exposes explicit functions rather than user-provided method properties.",
    "ecma262-22.1.3.13-0007": "Calling a custom matcher is JavaScript dynamic dispatch and is not an OCaml regex-library surface.",
    "ecma262-22.1.3.13-0009": "RegExpCreate from an arbitrary JavaScript argument is constructor/coercion behavior; OCaml callers compile regexps explicitly before match.",
    "ecma262-22.2.6.8-0003": "The non-object receiver TypeError branch is JavaScript runtime type checking; OCaml enforces regexp receiver types statically.",
    "ecma262-22.2.6.8-0023": "The function name property is JavaScript function-object metadata, not OCaml regex match semantics.",
}

MATCH_ALL_NON_OCAML_ROWS = {
    "ecma262-22.1.3.14-0004": "RequireObjectCoercible rejects JavaScript null/undefined receivers; OCaml string arguments are statically non-null.",
    "ecma262-22.1.3.14-0005": "The Object branch is JavaScript dynamic-dispatch setup; the OCaml match_all adapter takes an explicit compiled regexp.",
    "ecma262-22.1.3.14-0006": "IsRegExp is a JavaScript object/protocol brand check; OCaml callers pass an explicit compiled regexp.",
    "ecma262-22.1.3.14-0007": "The IsRegExp branch is JavaScript object-protocol dispatch setup, not an OCaml regex-library surface.",
    "ecma262-22.1.3.14-0008": "Getting the JavaScript flags property belongs to JS object protocol; OCaml flags are part of the compiled regexp value.",
    "ecma262-22.1.3.14-0009": "RequireObjectCoercible(flags) is JavaScript dynamic property validation and has no OCaml adapter equivalent.",
    "ecma262-22.1.3.14-0010": "String.prototype.matchAll's non-global RegExp TypeError is JavaScript method validation; the OCaml adapter exposes direct @@matchAll-style iteration over explicit regexps.",
    "ecma262-22.1.3.14-0011": "GetMethod(regexp, @@matchAll) is JavaScript method lookup and has no OCaml adapter equivalent.",
    "ecma262-22.1.3.14-0012": "The custom @@matchAll branch is JavaScript object protocol; OCaml exposes explicit functions rather than user-provided method properties.",
    "ecma262-22.1.3.14-0013": "Calling a custom matchAll matcher is JavaScript dynamic dispatch and is not an OCaml regex-library surface.",
    "ecma262-22.1.3.14-0015": "RegExpCreate from an arbitrary JavaScript argument is constructor/coercion behavior; OCaml callers compile regexps explicitly before match_all.",
    "ecma262-22.2.6.9-0003": "The non-object receiver TypeError branch is JavaScript runtime type checking; OCaml enforces regexp receiver types statically.",
    "ecma262-22.2.6.9-0005": "SpeciesConstructor is JavaScript constructor/prototype customization; the OCaml adapter models cloned matcher state without JS species dispatch.",
    "ecma262-22.2.6.9-0007": "Construct(C, R, flags) is JavaScript constructor dispatch; the OCaml adapter creates internal matcher state without invoking user constructors.",
    "ecma262-22.2.6.9-0015": "The function name property is JavaScript function-object metadata, not OCaml regex match_all semantics.",
}

SPLIT_NON_OCAML_ROWS = {
    "ecma262-22.1.3.23-0004": "RequireObjectCoercible rejects JavaScript null/undefined receivers; OCaml string arguments are statically non-null.",
    "ecma262-22.1.3.23-0005": "The Object branch is JavaScript dynamic-dispatch setup; the OCaml split adapter takes an explicit compiled regexp.",
    "ecma262-22.1.3.23-0006": "GetMethod(separator, @@split) is JavaScript method lookup and has no OCaml adapter equivalent.",
    "ecma262-22.1.3.23-0007": "The custom @@split branch is JavaScript object protocol; OCaml exposes explicit functions rather than user-provided method properties.",
    "ecma262-22.1.3.23-0008": "Calling a custom splitter is JavaScript dynamic dispatch and is not an OCaml regex-library surface.",
    "ecma262-22.1.3.23-0009": "The post-dispatch ToString receiver step belongs to String.prototype.split's non-RegExp separator path; the RegExp adapter receives an explicit string input.",
    "ecma262-22.1.3.23-0010": "The post-dispatch limit normalization belongs to String.prototype.split's non-RegExp separator path; RegExp split limit behavior is covered by RegExp.prototype[@@split].",
    "ecma262-22.1.3.23-0011": "ToString(separator) is plain string-separator behavior, not the explicit RegExp split adapter surface.",
    "ecma262-22.1.3.23-0012": "The plain String.prototype.split limit-zero branch is outside the RegExp adapter path; RegExp split has its own limit-zero row.",
    "ecma262-22.1.3.23-0013": "CreateArrayFromList for the plain string-separator limit-zero branch is JavaScript string API behavior, not the RegExp adapter surface.",
    "ecma262-22.1.3.23-0014": "The undefined-separator branch is String.prototype.split string API behavior and has no RegExp adapter equivalent.",
    "ecma262-22.1.3.23-0015": "Returning the whole string for an undefined separator is not RegExp split behavior.",
    "ecma262-22.1.3.23-0016": "separatorLength is plain string-separator state, not RegExp split behavior.",
    "ecma262-22.1.3.23-0017": "The empty string separator branch splits into code units without RegExp execution and is not the RegExp adapter surface.",
    "ecma262-22.1.3.23-0018": "strLen for the empty string separator branch is plain string API state, not RegExp split behavior.",
    "ecma262-22.1.3.23-0019": "outLen clamping for the empty string separator branch is plain string API behavior, not RegExp split behavior.",
    "ecma262-22.1.3.23-0020": "The empty string separator head substring is plain string API behavior, not RegExp split behavior.",
    "ecma262-22.1.3.23-0021": "Converting a plain string head into code units is String.prototype.split string-separator behavior, not RegExp split behavior.",
    "ecma262-22.1.3.23-0022": "Returning code units for an empty string separator is not RegExp split behavior.",
    "ecma262-22.1.3.23-0023": "The empty-input plain string separator branch is not the RegExp split empty-input branch.",
    "ecma262-22.1.3.23-0024": "The plain string-separator substring accumulator is outside the RegExp adapter path.",
    "ecma262-22.1.3.23-0025": "The plain string-separator scan index is outside the RegExp adapter path.",
    "ecma262-22.1.3.23-0026": "StringIndexOf over a plain separator is not RegExp execution.",
    "ecma262-22.1.3.23-0027": "The plain string-separator search loop is not RegExp split behavior.",
    "ecma262-22.1.3.23-0028": "The plain string-separator substring extraction is not RegExp split behavior.",
    "ecma262-22.1.3.23-0029": "Appending a substring from a plain string-separator split is not RegExp split behavior.",
    "ecma262-22.1.3.23-0030": "The plain string-separator limit check is not RegExp split behavior.",
    "ecma262-22.1.3.23-0031": "Advancing past a plain string separator is not RegExp split behavior.",
    "ecma262-22.1.3.23-0032": "Repeating StringIndexOf for a plain separator is not RegExp execution.",
    "ecma262-22.1.3.23-0033": "The final plain string-separator tail substring is not RegExp split behavior.",
    "ecma262-22.1.3.23-0034": "Appending the final plain string-separator tail is not RegExp split behavior.",
    "ecma262-22.1.3.23-0035": "Returning the plain string-separator split list is not RegExp split behavior.",
    "ecma262-22.2.6.14-0003": "The non-object receiver TypeError branch is JavaScript runtime type checking; OCaml enforces regexp receiver types statically.",
    "ecma262-22.2.6.14-0005": "SpeciesConstructor is JavaScript constructor/prototype customization; the OCaml adapter models cloned sticky matcher state without JS species dispatch.",
    "ecma262-22.2.6.14-0011": "Construct(C, rx, newFlags) is JavaScript constructor dispatch; the OCaml adapter creates internal sticky matcher state without invoking user constructors.",
    "ecma262-22.2.6.14-0053": "The function name property is JavaScript function-object metadata, not OCaml regex split semantics.",
}

ESCAPE_NON_OCAML_ROWS = {
    "ecma262-22.2.5.1-0003": "The non-String TypeError branch is JavaScript runtime type checking; OCaml escape adapters receive statically typed string or js_string inputs.",
}

REPLACE_NON_OCAML_ROWS = {
    **{
        f"ecma262-22.1.3.19-{index:04d}":
        "String.prototype.replace receiver dispatch and custom @@replace lookup are JavaScript method protocol; the OCaml adapter calls RegExp replacement semantics through an explicit compiled regexp."
        for index in range(1, 9)
    },
    **{
        f"ecma262-22.1.3.19-{index:04d}":
        "String.prototype.replace plain search-string branch is not RegExp replacement behavior; the OCaml adapter covers RegExp.prototype[@@replace] plus GetSubstitution."
        for index in range(9, 25)
    },
    **{
        f"ecma262-22.1.3.20-{index:04d}":
        "String.prototype.replaceAll receiver dispatch, RegExp global validation, and custom @@replace lookup are JavaScript method protocol; the OCaml replace_all helper is explicit and does not expose JS object dispatch."
        for index in range(1, 13)
    },
    **{
        f"ecma262-22.1.3.20-{index:04d}":
        "String.prototype.replaceAll plain search-string traversal is not RegExp replacement behavior; RegExp replacement is covered through RegExp.prototype[@@replace] and GetSubstitution."
        for index in range(13, 40)
    },
    "ecma262-22.2.6.11-0003": "The non-object receiver TypeError branch is JavaScript runtime type checking; OCaml enforces regexp receiver types statically.",
    "ecma262-22.2.6.11-0049": "The functional replacer branch is JavaScript Callable dispatch; the current OCaml replace adapter is the explicit string-template adapter.",
    "ecma262-22.2.6.11-0050": "Functional replacer argument-list construction is JavaScript Callable dispatch and is not part of the string-template OCaml replacement adapter.",
    "ecma262-22.2.6.11-0051": "Functional replacer named-capture argument branching belongs to JavaScript Callable dispatch, not the string-template OCaml replacement adapter.",
    "ecma262-22.2.6.11-0052": "Appending namedCaptures to functional replacer arguments is JavaScript Callable dispatch and has no string-template adapter equivalent.",
    "ecma262-22.2.6.11-0053": "Calling the functional replacer is JavaScript dynamic dispatch; OCaml does not hide this behind the string replacement API.",
    "ecma262-22.2.6.11-0054": "ToString of a functional replacer result is JavaScript Callable result coercion, not string-template replacement behavior.",
    "ecma262-22.2.6.11-0057": "ToObject(namedCaptures) is JavaScript object conversion; the OCaml adapter uses typed capture metadata for named substitution lookup.",
    "ecma262-22.2.6.11-0065": "The function name property is JavaScript function-object metadata, not OCaml regex replace semantics.",
}


def non_ocaml_search_policy(row: dict[str, str]) -> dict[str, str]:
    return {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "search_adapter_js_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": SEARCH_NON_OCAML_ROWS[row["requirement_id"]],
    }


def non_ocaml_match_policy(row: dict[str, str]) -> dict[str, str]:
    return {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "match_adapter_js_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": MATCH_NON_OCAML_ROWS[row["requirement_id"]],
    }


def non_ocaml_match_all_policy(row: dict[str, str]) -> dict[str, str]:
    return {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "match_all_adapter_js_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": MATCH_ALL_NON_OCAML_ROWS[row["requirement_id"]],
    }


def non_ocaml_split_policy(row: dict[str, str]) -> dict[str, str]:
    return {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "split_adapter_js_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": SPLIT_NON_OCAML_ROWS[row["requirement_id"]],
    }


def non_ocaml_escape_policy(row: dict[str, str]) -> dict[str, str]:
    return {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "regexp_escape_adapter_js_type_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": ESCAPE_NON_OCAML_ROWS[row["requirement_id"]],
    }


def non_ocaml_replace_policy(row: dict[str, str]) -> dict[str, str]:
    return {
        "surface_decision": "non_applicable_with_reason",
        "surface_area": "replace_adapter_js_object_protocol",
        "public_api_status": "not_ocaml_surface",
        "ocaml_artifact": "none",
        "coverage_action": "keep_policy_exclusion_evidence",
        "next_test_artifact": "product_surface_policy_decision",
        "decision_reason": REPLACE_NON_OCAML_ROWS[row["requirement_id"]],
    }


def policy_for(row: dict[str, str]) -> dict[str, str]:
    if row["requirement_id"] in REPLACE_NON_OCAML_ROWS:
        return non_ocaml_replace_policy(row)
    if row["requirement_id"] in ESCAPE_NON_OCAML_ROWS:
        return non_ocaml_escape_policy(row)
    if row["requirement_id"] in SPLIT_NON_OCAML_ROWS:
        return non_ocaml_split_policy(row)
    if row["requirement_id"] in MATCH_ALL_NON_OCAML_ROWS:
        return non_ocaml_match_all_policy(row)
    if row["requirement_id"] in MATCH_NON_OCAML_ROWS:
        return non_ocaml_match_policy(row)
    if row["requirement_id"] in SEARCH_NON_OCAML_ROWS:
        return non_ocaml_search_policy(row)
    policy = POLICIES.get(row["clause_id"])
    if policy is None:
        raise SystemExit(
            "missing product-surface policy for "
            f"{row['clause_id']} {row['clause_title']}"
        )
    decision = policy["surface_decision"]
    if decision not in ALLOWED_DECISIONS:
        raise SystemExit(
            f"invalid product-surface decision {decision!r} for {row['clause_id']}"
        )
    return policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirement-mapping",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    requirement_mapping = Path(args.requirement_mapping)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not requirement_mapping.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement mapping at {requirement_mapping}; "
            "run tools/build_ecma262_regexp_requirement_mapping.py first"
        )

    input_fieldnames, input_rows = read_tsv(requirement_mapping)
    required_columns = {"route_status", "clause_id", "clause_title"}
    missing_columns = required_columns.difference(input_fieldnames)
    if missing_columns:
        raise SystemExit(
            f"missing required columns in {requirement_mapping}: "
            + ", ".join(sorted(missing_columns))
        )

    rows = []
    for row in input_rows:
        if row["route_status"] != "needs_product_policy_decision":
            continue
        policy = policy_for(row)
        rows.append({**row, **policy, "surface_policy_state": "decided"})

    if not rows:
        raise SystemExit(
            f"no product-surface rows found in {requirement_mapping}; "
            "expected route_status=needs_product_policy_decision"
        )

    decision_counts = Counter(row["surface_decision"] for row in rows)
    public_api_counts = Counter(row["public_api_status"] for row in rows)
    surface_area_counts = Counter(row["surface_area"] for row in rows)
    artifact_counts = Counter(row["ocaml_artifact"] for row in rows)
    action_counts = Counter(row["coverage_action"] for row in rows)
    test_artifact_counts = Counter(row["next_test_artifact"] for row in rows)
    clause_counts = Counter(
        f"{row['clause_id']} {row['clause_title']}" for row in rows
    )

    undecided_rows = sum(1 for row in rows if row["surface_policy_state"] != "decided")
    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirement_mapping\t{requirement_mapping}\n",
        f"input_product_rows\t{len(rows)}\n",
        f"undecided_rows\t{undecided_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{str(args.dry_run).lower()}\n",
    ]
    for name, count in sorted(decision_counts.items()):
        summary_lines.append(f"surface_decision_{name}\t{count}\n")
    for name, count in sorted(public_api_counts.items()):
        summary_lines.append(f"public_api_status_{name}\t{count}\n")
    for name, count in sorted(surface_area_counts.items()):
        summary_lines.append(f"surface_area_{name}\t{count}\n")
    for name, count in sorted(artifact_counts.items()):
        summary_lines.append(f"ocaml_artifact_{name}\t{count}\n")
    for name, count in sorted(action_counts.items()):
        summary_lines.append(f"coverage_action_{name}\t{count}\n")
    for name, count in sorted(test_artifact_counts.items()):
        summary_lines.append(f"next_test_artifact_{name}\t{count}\n")
    for name, count in sorted(clause_counts.items()):
        summary_lines.append(f"clause_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        *input_fieldnames,
        "surface_policy_state",
        "surface_decision",
        "surface_area",
        "public_api_status",
        "ocaml_artifact",
        "coverage_action",
        "next_test_artifact",
        "decision_reason",
    ]
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))
    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
