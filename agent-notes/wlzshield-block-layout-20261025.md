# wlzshield encryptBlock layout

pid 46648 detail only. No array elements, joined text, or gunzip body.

```
source=rt_20261025092534_766ba10ee4/raw/jscall/trace_jscall_process_46648.detail.bin
encryptBlock argc=2 n=11 same_func=yes
layout=packed
sparse_misaligned=no
prefix_identical_11=false

arg0_len truncated arg1 nz_bytes low_byte_only high_byte_only lanes_hi_to_lo
368 true 0 1461 false false 365,364,367,365
368 true 4 1461 false false 365,364,367,365
368 true 8 1461 false false 365,364,367,365
368 true 12 1461 false false 365,364,367,365
368 true 16 1461 false false 365,364,367,365
368 true 20 1461 false false 365,364,367,365
368 true 24 1461 false false 365,364,367,365
367 true 28 1457 false false 364,363,366,364
368 true 32 1461 false false 365,364,367,365
368 true 36 1461 false false 365,364,367,365
367 true 40 1457 false false 364,363,366,364

len_groups=368x9,367x2
words_with_only_low_or_only_high_byte=0
sparse_column=not_extracted
gzip_magic=n/a brace8=n/a gunzip=n/a
adjacent_calls_differ=8_contiguous_words_from_arg1
overlap_outside_that_window=equal

encrypt argc=3 n=1 only_object_tag=true array=false string=false
encrypt argc=4 n=1 only_object_tag=true array=false string=false
```

CryptoJS big-endian split of each int32. Both length groups use all four byte lanes. The 367-length rows are the arg1=28 and arg1=40 captures. Column gzip checks do not apply.
