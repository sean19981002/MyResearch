> # 10/4 Meeting # 
> +  10/7，將 9/26 ~ 10/3 的 retweeters 全部抓下來
> + 10/3 ~ 10/10 的 tweets 抓下來，10/13 抓 retweet 
> + predict 72hr 是否 retweet

> # 10/6 #
> + Tweepy v2 等了 29 次 869 秒，抓取 retweeters 執行了 7.28 小時。

> # 10/7
> - 將資料抓取完畢
> - 已經將 retweers id encoding 成 0,1,2,3...
> - 已經將 user 取聯集，把重複的 id 過濾掉，存成 set

> # 10/8
> - 將 get_retweeters 以 multi-threading 的方式呈現，共 7 個可用的 tokens，所以 thread 數為 7。

> # 10/10
> - retweeters 以 multi-threading 的方式抓取，Thread = 8，255 min。
> - 71000 多個 user，找 follower 很吃力，先篩選 target user。
> - target user：
>   + 把 user 轉推多少篇推文的分佈用出來
>   + 設一個 bound 
>   + 把低於 bound 的 users 剔除，剩下的就是我們的 target users

> # 10/11 Meeting
> - 抓 retweeters 轉推的那篇推文的 timestamp
> - Dict 要先用 json.dumps，再寫入 json
> - 把 target users 找出來
> * json 儲存多個 objects 要提取出來 !!!
> - Negative Sampling 我可能需要引進
> - 提取 timestamp 可能會非常花時間，因為每個 user 的活動情況(retweet)不一樣
> - 針對後面(predict data)的 tweet，要抓 active/inactive，把 retweeters 找出來，再去他們的牆上找出他們 retweet 的那篇 ID，比對 timestamp，是否在三天內 retweet，是的話才能算 retweet

> - ### 學長：
>   + 盡快處理 biden dataset 的 active, inactive
>   + hashtag 維度降低
>   + 看能否調整 base graph 的 edge weight，看能不能多一點東西進來(e.x. retweet數，朋友數...等等) 
>   + negative sampling
>   + 12 小時裡面已經確定 retweet，加上 model 預測的 active/inactive，才是對的 -> 目標二
>   + 抓取 active/inactive 的時間點：6, 9, 12, 15, 18, 24, 30, 36, 42, 48, 54, 60 hr.

> # 10/13 Meeting
>   + 前七天的 tweet (57) 抓下來
>       - retweeters 抓下來，找出 target users (retweet 少於5篇的刪除)
>       - 找 target users 和 follow list
>       - follow 關係建 base graph(一張)
>
>   + 後七天的 tweet 抓下來
>       - 再看 target users(User tweets crawling) 的 retweet 時間
>       - 建出 12 * tweets 張 data graph 
>       - 12 個時間點：6, 9, 12, 15, 18, 24, 30, 36, 42, 48, 54, 60 hr.
>       - 用 active/inactive 的關係建 data graph

> # 10/17
>   + functions.py :
>       1. 使用 target users 的 id，去抓取每個 target user 牆上的 tweet。
>       2. 抓出 reference id，將多餘字元去除。
>       3. 比對 reference id 是否 in 那 57 篇 Biden tweets，有的話建成 list，將 此篇推文的 id, timestamp, reference id 存進list，再將此 list 存進另外一個 list。
>       4. 每抓完一個 user 的資料，將上述二維的 list 指派進 dict，此 dict 的 key 為 id of this target user。
>       5. 寫入一次檔案

> # 11/8 Meeting
>   + ### 記得把 base data 用好才上 model。
>   + ### 跟學長學 GConv，要如何重現結果