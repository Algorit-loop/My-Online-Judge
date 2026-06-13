(function() {
    'use strict';
    var currentLang = null;

    // ========================
    // Word lists per language
    // ========================
    var COMPLETIONS = {
        c_cpp: {
            keywords: [
                // C keywords
                'auto','break','case','char','const','continue','default','do',
                'double','else','enum','extern','float','for','goto','if',
                'inline','int','long','register','return','short','signed',
                'sizeof','static','struct','switch','typedef','union','unsigned',
                'void','volatile','while',
                // C++ keywords
                'alignas','alignof','and','and_eq','asm','bitand','bitor',
                'bool','catch','class','compl','concept','consteval','constexpr',
                'constinit','const_cast','co_await','co_return','co_yield',
                'decltype','delete','dynamic_cast','explicit','export',
                'false','friend','mutable','namespace','new','noexcept',
                'not','not_eq','nullptr','operator','or','or_eq',
                'private','protected','public','reinterpret_cast',
                'requires','static_assert','static_cast','template',
                'this','thread_local','throw','true','try','typeid',
                'typename','using','virtual','wchar_t','xor','xor_eq',
                'override','final'
            ],
            types: [
                'int8_t','int16_t','int32_t','int64_t',
                'uint8_t','uint16_t','uint32_t','uint64_t',
                'size_t','ptrdiff_t','intptr_t','uintptr_t',
                'string','wstring','string_view',
                'vector','deque','list','forward_list','array',
                'map','multimap','unordered_map','unordered_multimap',
                'set','multiset','unordered_set','unordered_multiset',
                'pair','tuple','optional','variant','any',
                'stack','queue','priority_queue',
                'bitset','valarray',
                'shared_ptr','unique_ptr','weak_ptr',
                'function','reference_wrapper',
                'complex','ratio','chrono',
                'stringstream','istringstream','ostringstream',
                'ifstream','ofstream','fstream',
                'istream','ostream','iostream'
            ],
            stdlib: [
                // I/O
                'cout','cin','cerr','clog','endl','flush',
                'getline','printf','scanf','puts','gets','putchar','getchar',
                'sprintf','sscanf','fprintf','fscanf',
                // STL algorithms
                'sort','stable_sort','partial_sort','nth_element',
                'lower_bound','upper_bound','equal_range','binary_search',
                'find','find_if','find_if_not','count','count_if',
                'for_each','transform','copy','copy_if','copy_n',
                'fill','fill_n','generate','generate_n',
                'remove','remove_if','remove_copy','remove_copy_if',
                'replace','replace_if','replace_copy','replace_copy_if',
                'reverse','reverse_copy','rotate','rotate_copy',
                'unique','unique_copy',
                'merge','inplace_merge',
                'set_union','set_intersection','set_difference','set_symmetric_difference',
                'min','max','minmax','min_element','max_element','minmax_element',
                'clamp','swap','iter_swap',
                'accumulate','inner_product','partial_sum','adjacent_difference',
                'iota','reduce','inclusive_scan','exclusive_scan',
                'next_permutation','prev_permutation',
                'is_sorted','is_sorted_until',
                'all_of','any_of','none_of',
                'lexicographical_compare',
                // Container methods
                'push_back','pop_back','push_front','pop_front',
                'emplace_back','emplace_front','emplace',
                'insert','erase','clear','resize','reserve','shrink_to_fit',
                'begin','end','rbegin','rend','cbegin','cend',
                'front','back','at','data',
                'size','empty','capacity','max_size',
                'top','push','pop','enqueue','dequeue',
                'first','second',
                'make_pair','make_tuple','tie','get',
                // String methods
                'substr','find','rfind','find_first_of','find_last_of',
                'find_first_not_of','find_last_not_of',
                'append','assign','compare','replace',
                'c_str','length','npos',
                'stoi','stol','stoll','stoul','stoull','stof','stod','stold',
                'to_string',
                // Math
                'abs','fabs','ceil','floor','round','trunc',
                'pow','sqrt','cbrt','hypot',
                'log','log2','log10','exp','exp2',
                'sin','cos','tan','asin','acos','atan','atan2',
                'gcd','lcm',
                // Memory
                'memset','memcpy','memmove','memcmp',
                'malloc','calloc','realloc','free',
                // Utility
                'move','forward','declval',
                'make_shared','make_unique',
                'static_pointer_cast','dynamic_pointer_cast',
                'numeric_limits','INT_MAX','INT_MIN','LLONG_MAX','LLONG_MIN',
                'INFINITY','NAN',
                'assert','exit','abort',
                'clock','time','difftime',
                'srand','rand'
            ],
            headers: [
                '#include <bits/stdc++.h>',
                '#include <iostream>',
                '#include <algorithm>',
                '#include <vector>',
                '#include <string>',
                '#include <map>',
                '#include <set>',
                '#include <unordered_map>',
                '#include <unordered_set>',
                '#include <queue>',
                '#include <stack>',
                '#include <deque>',
                '#include <list>',
                '#include <array>',
                '#include <bitset>',
                '#include <cmath>',
                '#include <cstdio>',
                '#include <cstdlib>',
                '#include <cstring>',
                '#include <climits>',
                '#include <numeric>',
                '#include <functional>',
                '#include <utility>',
                '#include <cassert>',
                '#include <sstream>',
                '#include <fstream>',
                '#include <iomanip>',
                '#include <tuple>',
                '#include <memory>',
                '#include <chrono>',
                '#include <random>',
                '#include <regex>',
                'using namespace std;'
            ]
        },

        python: {
            keywords: [
                'False','None','True','and','as','assert','async','await',
                'break','class','continue','def','del','elif','else','except',
                'finally','for','from','global','if','import','in','is','lambda',
                'nonlocal','not','or','pass','raise','return','try','while',
                'with','yield','match','case'
            ],
            stdlib: [
                // Built-in functions
                'print','input','len','range','int','float','str','bool',
                'list','dict','set','tuple','type','isinstance','issubclass',
                'sorted','reversed','enumerate','zip','map','filter',
                'sum','min','max','abs','round','pow','divmod','hash',
                'id','repr','chr','ord','hex','oct','bin','format',
                'iter','next','any','all','callable','dir','vars','globals','locals',
                'open','super','property','classmethod','staticmethod',
                'getattr','setattr','delattr','hasattr',
                'complex','bytes','bytearray','memoryview','frozenset',
                'slice','object','exec','eval','compile',
                // List/dict/set/str methods
                'append','extend','insert','remove','pop','index','count',
                'sort','reverse','copy','clear',
                'keys','values','items','get','update','setdefault','popitem',
                'add','discard','union','intersection','difference','symmetric_difference',
                'issubset','issuperset','isdisjoint',
                'join','split','rsplit','strip','lstrip','rstrip',
                'replace','find','rfind','startswith','endswith',
                'upper','lower','title','capitalize','swapcase',
                'isdigit','isalpha','isalnum','isspace','isupper','islower',
                'encode','decode','format','center','ljust','rjust','zfill',
                // Common modules
                'math','sys','os','re','json','collections','itertools',
                'functools','operator','bisect','heapq','random','string',
                'datetime','time','copy','io','struct','typing',
                // collections
                'defaultdict','Counter','deque','OrderedDict','namedtuple','ChainMap',
                // itertools
                'product','permutations','combinations','combinations_with_replacement',
                'chain','cycle','repeat','accumulate','groupby','starmap',
                // heapq
                'heappush','heappop','heapify','heapreplace','nlargest','nsmallest',
                // bisect
                'bisect_left','bisect_right','insort_left','insort_right',
                // math
                'ceil','floor','sqrt','log','log2','log10','exp','pow',
                'gcd','lcm','factorial','comb','perm','isqrt',
                'pi','inf','nan','e',
                // functools
                'lru_cache','cache','reduce','partial','wraps',
                // typing
                'List','Dict','Set','Tuple','Optional','Union','Any',
                'Callable','Iterator','Generator','Sequence','Mapping',
                // sys
                'stdin','stdout','stderr','maxsize','setrecursionlimit',
                // Common patterns
                'if __name__',
                '__init__','__str__','__repr__','__len__','__getitem__',
                '__setitem__','__delitem__','__iter__','__next__',
                '__eq__','__lt__','__gt__','__le__','__ge__','__hash__',
                '__enter__','__exit__','__call__'
            ]
        },

        java: {
            keywords: [
                'abstract','assert','boolean','break','byte','case','catch',
                'char','class','const','continue','default','do','double',
                'else','enum','extends','final','finally','float','for',
                'goto','if','implements','import','instanceof','int',
                'interface','long','native','new','package','private',
                'protected','public','return','short','static','strictfp',
                'super','switch','synchronized','this','throw','throws',
                'transient','try','void','volatile','while','var','record',
                'sealed','permits','yield'
            ],
            types: [
                'String','StringBuilder','StringBuffer',
                'Integer','Long','Double','Float','Character','Boolean','Byte','Short',
                'BigInteger','BigDecimal',
                'Object','Class','Enum',
                'ArrayList','LinkedList','Vector',
                'HashMap','TreeMap','LinkedHashMap','Hashtable','ConcurrentHashMap',
                'HashSet','TreeSet','LinkedHashSet',
                'PriorityQueue','ArrayDeque','Stack','Queue','Deque',
                'List','Map','Set','Collection','Iterable','Iterator',
                'Comparable','Comparator','Runnable','Callable',
                'Optional','Stream',
                'Scanner','BufferedReader','InputStreamReader','PrintWriter',
                'FileReader','FileWriter','File','Path','Paths',
                'IOException','Exception','RuntimeException',
                'NullPointerException','IndexOutOfBoundsException',
                'NumberFormatException','IllegalArgumentException',
                'StringBuilder','StringJoiner','StringTokenizer',
                'Random','Collections','Arrays','Math','System',
                'Thread','Executor','ExecutorService','Future'
            ],
            stdlib: [
                // System
                'System.out.println','System.out.print','System.out.printf',
                'System.in','System.err','System.exit','System.currentTimeMillis',
                // String methods
                'length','charAt','substring','indexOf','lastIndexOf',
                'contains','isEmpty','isBlank','trim','strip',
                'toLowerCase','toUpperCase','toCharArray','split',
                'equals','equalsIgnoreCase','compareTo','format',
                'valueOf','toString','parseInt','parseLong','parseDouble',
                'replace','replaceAll','matches','startsWith','endsWith',
                // Collection methods
                'add','remove','get','set','size','clear','contains','isEmpty',
                'iterator','stream','toArray','addAll','removeAll','retainAll',
                'put','putIfAbsent','getOrDefault','containsKey','containsValue',
                'keySet','values','entrySet',
                'push','pop','peek','poll','offer','element',
                // Arrays
                'Arrays.sort','Arrays.fill','Arrays.copyOf','Arrays.asList',
                'Arrays.binarySearch','Arrays.toString','Arrays.deepToString',
                'Arrays.stream','Arrays.compare',
                // Collections
                'Collections.sort','Collections.reverse','Collections.shuffle',
                'Collections.min','Collections.max','Collections.frequency',
                'Collections.unmodifiableList','Collections.synchronizedList',
                'Collections.emptyList','Collections.singletonList',
                // Math
                'Math.abs','Math.max','Math.min','Math.pow','Math.sqrt',
                'Math.ceil','Math.floor','Math.round','Math.log','Math.log10',
                'Math.PI','Math.E','Math.random',
                // Scanner
                'nextInt','nextLong','nextDouble','nextLine','nextFloat',
                'next','hasNext','hasNextInt','hasNextLine','hasNextDouble',
                // I/O
                'readLine','write','flush','close',
                'BufferedReader','InputStreamReader',
                // Stream
                'filter','map','reduce','collect','forEach','sorted',
                'distinct','limit','skip','count','anyMatch','allMatch','noneMatch',
                'flatMap','mapToInt','mapToLong','mapToDouble',
                'Collectors.toList','Collectors.toSet','Collectors.toMap',
                'Collectors.joining','Collectors.groupingBy',
                // Common
                'equals','hashCode','clone','getClass','notify','notifyAll','wait',
                // Imports
                'import java.util.*',
                'import java.io.*',
                'import java.util.stream.*',
                'import java.math.*'
            ]
        }
    };

    // ========================
    // Build CM6 completion objects
    // ========================
    function buildCompletions(lang) {
        var data = COMPLETIONS[lang];
        if (!data) return [];
        var result = [];
        var i;

        if (data.keywords) {
            for (i = 0; i < data.keywords.length; i++) {
                result.push({ label: data.keywords[i], type: 'keyword' });
            }
        }
        if (data.types) {
            for (i = 0; i < data.types.length; i++) {
                result.push({ label: data.types[i], type: 'type' });
            }
        }
        if (data.stdlib) {
            for (i = 0; i < data.stdlib.length; i++) {
                result.push({ label: data.stdlib[i], type: 'function' });
            }
        }
        if (data.headers) {
            for (i = 0; i < data.headers.length; i++) {
                result.push({ label: data.headers[i], type: 'text', boost: -1 });
            }
        }
        return result;
    }

    var cachedCompletions = {};
    function getCompletions(lang) {
        if (!cachedCompletions[lang]) {
            cachedCompletions[lang] = buildCompletions(lang);
        }
        return cachedCompletions[lang];
    }

    // ========================
    // Completion source for CM6
    // ========================
    window.CM6_completionSource = function(context) {
        // Match word characters, #, <, >, ., :
        var word = context.matchBefore(/[#\w][\w.<>:*]*/);
        if (!word && !context.explicit) return null;
        if (word && word.text.length < 2 && !context.explicit) return null;

        var completions = getCompletions(currentLang);
        if (!completions.length) return null;

        return {
            from: word ? word.from : context.pos,
            options: completions,
            validFor: /^[#\w][\w.<>:*]*$/
        };
    };

    window.CM6_updateLang = function(aceMode) {
        currentLang = aceMode;
    };
})();
