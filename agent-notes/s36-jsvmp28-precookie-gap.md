# 28 pre-cookie host shapes

Run `rt_20261024005551_a5cd2fe0e2`, page thread 0. The sealing cookie write is native `cookie` argc 1 at seq 6505, depth 8, inside frame 5066. Turn root is seq 5056, depth 1, parent 0. Seq 5057 is only the depth-2 callee. Every thread-0 seq in `(5056, 6505]` is inside that root. DOM get/set/call below are those whose `origin_call_id` is in the turn and whose DOM order is before the cookie set. `port`, `onmessage`, `start`, and `postMessage` begin at seq 6512 and are out of scope. `protocol`, `host`, and `pathname` are not read before the cookie write.

Counts are repeats of the same return class. Object tags are the tracer preview (`[object …]` length), not a second page read. No argument or cookie text is stored here.

| order | property | op | return shape | sandbox |
| --- | --- | --- | --- | --- |
| 1 | `window` | get ×10 | object, class Proxy | realm global, same object as `self` |
| 2 | `self` | get ×1 | object, class Proxy | same realm global |
| 3 | `location` | get ×1 | object, class Location | Proxy over a plain location bag; `toStringTag` off unless `SPIDER_TOSTRING_TAG=1` |
| 4 | `document` | get ×9 | object, class HTMLDocument | Proxy over a document stub whose prototype name is HTMLDocument |
| 5 | `createElement` | call ×2 | object, class HTMLAnchorElement, object-tag length 26; arg tag `a` | Proxy; tag forced to `A`; brand off by default |
| 6 | `setAttribute` | call ×1 | undefined; name `id`, value length 17 | undefined; stores the attribute |
| 7 | `documentElement` | get ×2 | object, class HTMLHtmlElement, object-tag length 24 | Proxy of `element("html")`, `tagName` `DIV`, not an HTMLHtmlElement |
| 8 | `appendChild` | call ×1 | object, class HTMLAnchorElement; receiver HTMLHtmlElement | returns the child it was given |
| 9 | `removeChild` | call ×1 | object, class HTMLAnchorElement, object-tag length 26; receiver HTMLHtmlElement | returns the child it was given |
| 10 | `href` | set ×1 | raw `testpath` | URL setter against the challenge href |
| 11 | `href` | get ×2 | string length 66 | same resolution, length 66 |
| 12 | `all` | get ×2 | object, class HTMLAllCollection; one slot class Proxy; bracket preview length 19 | HTMLDDA object branded HTMLAllCollection |
| 13 | `navigator` | get ×1 | object, class Navigator, object-tag length 18 | Proxy over a plain bag; `toStringTag` off by default |
| 14 | `webdriver` | get ×1 | bool false | bool false |
| 15 | `encode` | call ×1 | Uint8Array length 63; arg string length 63, all code points below 128 | in-realm TextEncoder, same byte length for that input |

Matched shapes, not the next cut: `href` length 66, `webdriver` false, `setAttribute` undefined, `encode` Uint8Array length 63, `appendChild` / `removeChild` returning the child. Already measured and not repeated: `document.all` HTMLDDA, uppercase tag `A`, in-realm TextEncoder. `protocol` / `host` / `pathname` have no pre-cookie read.

Next surface: `document.documentElement` get. It is read twice before the cookie write and is the `appendChild` / `removeChild` receiver. The trace return is an HTMLHtmlElement (object-tag length 24). The sandbox return is a Proxy of a generic element whose `tagName` is `DIV`. One falsifier: change only that getter so the return is an HTMLHtmlElement with tag `HTML` and object-tag length 24. If the sealed token id does not move, this class is not the fork.
