# cowin_slot_notification
Python script to send mail and slack notification for vaccination slot at cowin

## Input
The script takes input from `user_info.json`, mutliple inputs can be given as pincodes and disctrict_ids in the json, the schema is as follows
```
[
  { "name":"<user_name>"
    "email":"<email_to_notify>"
    "slack":"<slack_user_id>"
    "pincode":[<list_of_pincodes>]
    "district":[<list_of_districts>]
  },
  {...},
  ...
  ...
]
```

## Environment variable
Two environment variable needs to be setup for script to work properly, follow instructions given in the links
1. slack webhook -> https://api.slack.com/messaging/webhooks
2. Gmail app password -> https://support.google.com/accounts/answer/185833?hl=en

export environment variable as follows:
```
export slack_webhook="xxxxxx"
export gmail_pass="xxxxx"
```
