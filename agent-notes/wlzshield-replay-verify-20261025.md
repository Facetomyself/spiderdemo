# wlzshield replay verify

packet=000105 challenge POST
body_bytes=41958
body_matches_content_length=True
vendor_cookie=absent
fields=vendor_http,vendor_msg,token_len,token_alnum,site_http,success,site_category,page_data_len

page=2 vendor_http=200 vendor_msg=认证成功 token_len=268 token_alnum=false site_http=200 success=False site_category=其他 page_data_len=0
page=3 vendor_http=200 vendor_msg=认证成功 token_len=268 token_alnum=false site_http=200 success=False site_category=其他 page_data_len=0

## shape page=2
site_keys=error,success
error=IP地址不匹配
message=absent
token_len=268
token_dot=0
token_eq=0
token_plus=0
token_slash=0
token_eyJ=false
token_alnum_ratio=0.9664
