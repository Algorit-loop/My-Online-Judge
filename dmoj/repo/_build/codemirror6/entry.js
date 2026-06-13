// CodeMirror 6 IDE Bundle for ALOJ
// Exports everything under window.CM6

// Core
import { EditorState, Compartment } from '@codemirror/state';
import {
    EditorView, keymap, lineNumbers, highlightActiveLine,
    highlightActiveLineGutter, drawSelection, dropCursor,
    rectangularSelection, crosshairCursor
} from '@codemirror/view';
import {
    defaultKeymap, history, historyKeymap, indentWithTab,
    undo, redo
} from '@codemirror/commands';
import {
    syntaxHighlighting, defaultHighlightStyle, indentOnInput,
    bracketMatching, foldGutter, foldKeymap, StreamLanguage,
    HighlightStyle
} from '@codemirror/language';
import {
    autocompletion, closeBrackets, closeBracketsKeymap,
    completionKeymap, acceptCompletion
} from '@codemirror/autocomplete';
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search';
import { tags } from '@lezer/highlight';

// Native language packages
import { cpp } from '@codemirror/lang-cpp';
import { python } from '@codemirror/lang-python';
import { java } from '@codemirror/lang-java';
import { javascript } from '@codemirror/lang-javascript';
import { rust } from '@codemirror/lang-rust';
import { php } from '@codemirror/lang-php';
import { markdown } from '@codemirror/lang-markdown';

// Theme
import { oneDark } from '@codemirror/theme-one-dark';

// Legacy modes
import { pascal } from '@codemirror/legacy-modes/mode/pascal';
import { ruby } from '@codemirror/legacy-modes/mode/ruby';
import { perl } from '@codemirror/legacy-modes/mode/perl';
import { csharp, kotlin, scala, dart, objectiveC } from '@codemirror/legacy-modes/mode/clike';
import { haskell } from '@codemirror/legacy-modes/mode/haskell';
import { go } from '@codemirror/legacy-modes/mode/go';
import { swift } from '@codemirror/legacy-modes/mode/swift';
import { lua } from '@codemirror/legacy-modes/mode/lua';
import { d } from '@codemirror/legacy-modes/mode/d';
import { coffeeScript } from '@codemirror/legacy-modes/mode/coffeescript';
import { fortran } from '@codemirror/legacy-modes/mode/fortran';
import { scheme } from '@codemirror/legacy-modes/mode/scheme';
import { groovy } from '@codemirror/legacy-modes/mode/groovy';
import { oCaml, fSharp } from '@codemirror/legacy-modes/mode/mllike';
import { vb } from '@codemirror/legacy-modes/mode/vb';
import { gas } from '@codemirror/legacy-modes/mode/gas';
import { tcl } from '@codemirror/legacy-modes/mode/tcl';
import { cobol } from '@codemirror/legacy-modes/mode/cobol';
import { commonLisp } from '@codemirror/legacy-modes/mode/commonlisp';

window.CM6 = {
    // Core
    EditorState,
    EditorView,
    Compartment,

    // View
    keymap,
    lineNumbers,
    highlightActiveLine,
    highlightActiveLineGutter,
    drawSelection,
    dropCursor,
    rectangularSelection,
    crosshairCursor,

    // Commands
    defaultKeymap,
    history,
    historyKeymap,
    indentWithTab,
    undo,
    redo,

    // Language
    syntaxHighlighting,
    defaultHighlightStyle,
    indentOnInput,
    bracketMatching,
    foldGutter,
    foldKeymap,
    StreamLanguage,
    HighlightStyle,
    tags,

    // Autocomplete
    autocompletion,
    closeBrackets,
    closeBracketsKeymap,
    completionKeymap,
    acceptCompletion,

    // Search
    searchKeymap,
    highlightSelectionMatches,

    // Native languages
    cpp,
    python,
    java,
    javascript,
    rust,
    php,
    markdown,

    // Theme
    oneDark,

    // Legacy modes (grouped)
    legacyModes: {
        pascal,
        ruby,
        perl,
        csharp,
        kotlin,
        scala,
        dart,
        objectiveC,
        haskell,
        go,
        swift,
        lua,
        d,
        coffeeScript,
        fortran,
        scheme,
        groovy,
        oCaml,
        fSharp,
        vb,
        gas,
        tcl,
        cobol,
        commonLisp
    }
};
