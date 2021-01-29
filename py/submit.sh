host=$1
diffid=$2
token=$3

cookie=$(cat ~/.config/phabrik/cookie.txt)

url="${host}/differential/revision/edit/${diffid}/comment/"

curl ${url} \
  -H 'Connection: keep-alive' \
  -H "X-Phabricator-Csrf: ${token}" \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36' \
  -H "X-Phabricator-Via: /D${diffid}" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Accept: */*' \
  -H "Origin: ${host}" \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Accept-Language: en-GB,en-US;q=0.9,en;q=0.8' \
  -H "Cookie: ${cookie}" \
  --data-raw '__form__=1' \
  --compressed

