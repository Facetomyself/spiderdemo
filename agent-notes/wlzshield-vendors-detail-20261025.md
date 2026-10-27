# wlzshield vendors detail shape

```
runId=rt_20261025092534_766ba10ee4
caseId=spiderdemo-register-login
integrity=pass
state=stopped
finishedAt=2026-10-25T09:33:38.287Z
http:
seq=31 route=init method=GET status=401 msg=need_login wsToken.len=absent wlzData.len=absent wlzData.p1=absent page_num=absent page_data.len=absent
seq=104 route=init method=GET status=200 msg=其他 page_data.len=10 kind=list wsToken.len=absent wlzData.len=absent wlzData.p1=absent page_num=absent
seq=105 route=challenge method=POST status=200 msg=认证成功 wlzData.len=41855 wlzData.p1=yes wsToken.len=352 page_num=absent page_data.len=absent
seq=106 route=challenge method=OPTIONS status=204 msg=其他 wsToken.len=absent wlzData.len=absent wlzData.p1=absent page_num=absent page_data.len=absent
seq=107 route=verify method=POST status=200 msg=验证成功 page_num=2 wlz_token.len=352 page_data.len=10 kind=list wsToken.len=absent wlzData.len=absent wlzData.p1=absent
jscall:
pid=11172 bin=trace_jscall_process_11172.bin detail=no records=0 trailing=0
pid=13636 bin=trace_jscall_process_13636.bin detail=no records=0 trailing=0
pid=21052 bin=trace_jscall_process_21052.bin detail=no records=0 trailing=0
pid=40436 bin=trace_jscall_process_40436.bin detail=no records=0 trailing=0
pid=44740 bin=trace_jscall_process_44740.bin detail=no records=0 trailing=0
pid=46648 bin=trace_jscall_process_46648.bin detail=yes records=7240 trailing=0
pid=46648 vendorsFuncs=226 detailCalls=7240 detailSlots=21857 dropped=dropped_chunks=0 dropped_gate=611 dropped_limit=0 dropped_no_func_id=0 opcode_dropped_limit=0
pid=46648 encryptShapedDetailCalls=17 detailWordsField=0 detailSigBytesField=0
cryptoShapes:
  n=9 encryptBlock argc=2 ok=True detail=yes | this object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg0 array len=368 trunc=yes | arg1 int32 | return undefined len=0
  n=2 7165/r.Cipher<._createHelper< argc=0 ok=True detail=yes | this undefined bytes=0 | return function len=8
  n=2 7165/r.Cipher<._createHelper argc=1 ok=True detail=yes | this object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg0 object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | return object len=6
  n=2 encryptBlock argc=2 ok=True detail=yes | this object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg0 array len=367 trunc=yes | arg1 int32 | return undefined len=0
  n=1 encrypt argc=4 ok=True detail=yes | this object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg0 object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg1 object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg2 object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg3 object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | return object len=6
  n=1 encrypt argc=3 ok=True detail=yes | this object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg0 object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg1 object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | arg2 object tag=Object props=no hasWords=no hasSigBytes=no bytes=6 | return object len=6
fallbackTop25=skipped encryptShapedDetail=yes
pid=49372 bin=trace_jscall_process_49372.bin detail=no records=0 trailing=0
pid=53652 bin=trace_jscall_process_53652.bin detail=no records=0 trailing=0
pid=55108 bin=trace_jscall_process_55108.bin detail=no records=0 trailing=0
pid=55340 bin=trace_jscall_process_55340.bin detail=no records=0 trailing=0
pid=58220 bin=trace_jscall_process_58220.bin detail=no records=0 trailing=0
decrypt:
challengeBlobs=1 keyIvPairs=0
decryptOk=no errorClass=nokeyiv keyIvSigBytes16=absent
```
