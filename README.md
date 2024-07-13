# Ghotona API: backend server for Ghotona Chitro

This is the repository for the backend server for <a href="github.com/shafin-r/ghotona-chitro">Ghotona Chitro</a>, a web application designed to find out events and other hidden insights from Bengali news text corpora.

## Usage

There are mainly five API endpoints you can access in version 0.0.1.

### Login

To login to the API, you need to send a `POST` request to the endpoint below:

```
http://localhost:5000/login
```

The `POST` request should contain your email address and password in a JSON format like this:

```
{
    "email": "shafin@gmail.com",
    "password": "test1234"
}
```

Upon successful access, you will get the following JSON document containing your `first_name`, `last_name`, `token` and your `user_id` for the mongoose database.

```
{
    "first_name": "Shafin",
    "last_name": "Rahman",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcyMDkwMTkzOCwianRpIjoiOWJhZTdmYzktMDMzZC00ZWFmLTg2YTctYjllZmEwNjVkODdlIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJlbWFpbCI6InNoYWZpbjgwOHNAZ21haWwuY29tIn0sIm5iZiI6MTcyMDkwMTkzOCwiY3NyZiI6IjQ0ZTA0MzcyLTE4YzAtNDM3NC1iMGY0LWFmNTlhNThmY2VhMiIsImV4cCI6MTcyMDkyMzUzOH0.GbzIRebsrfjeMa9TkaR4jrebg6hKBoOMCz57Ds452PQ",
    "user_id": "667987fb293bcb6b67abf2d7"
}
```

### Register

You can create a new account on this API by sending a `POST` request to this endpoint:

```
http://localhost:5000/register
```

The `POST` request should contain the following information in a JSON format like this:

```
{
    "first_name": "Shafin",
    "last_name": "Rahman",
    "email": "shafin@gmail.com",
    "password": "test1234",
    "confirm_password": "test1234"
}
```

Upon successful registration, you will receive a `201` status code for confirmed creation of a new user.

### Logout

To logout of your account, you will have to send a `POST` request to this endpoint:

```
http://localhost:5000/logout
```

The `POST` request must have the `token` you received from when you logged into your account in the `Authorization` header of the request. Make sure that the `Authorization` method is set to `Bearer {token}`.

### Fetch Event Logs

You can fetch all of the events you have processed by sending a `POST` request to this endpoint:

```
http://localhost:5000/fetch-log
```

The `POST` request must have the `token` of your account along with your `user_id` that identifies your logs in the database. Please make sure that the `Authorization` method is set to `Bearer {token}`

```
{
  "user_id": "667987fb293bcb6b67abf2d7"
}
```

Upon successful access, you will receive a JSON document of all the logs processed by your account.

### Make a prediction

If you want to use our models to infer the event and other hidden insights, you will have to send a `POST` request to this endpoint:

```
http://localhost:5000/predict
```

The `POST` request must have the `token` of your account along with your `user_id` and `input` news that you want to infer. Please make sure that the `Authorization` method is set to `Bearer {token}`.

```
{
    "input": "দূরপাল্লার ক্ষেপণাস্ত্র মোতায়েনকে কেন্দ্র করে যুক্তরাষ্ট্র ও রাশিয়ার মধ্যে সম্প্রতি উত্তেজনা বেড়ে গেছে। এ উত্তেজনা থেকে পরিস্থিতি বিপজ্জনক সংঘাতের দিকে মোড় নিতে পারে। তাই উত্তেজনা কমাতে রুশ প্রতিরক্ষামন্ত্রী আন্দ্রেই বেলুসভ ও যুক্তরাষ্ট্রের পররাষ্ট্রমন্ত্রী লয়েড অস্টিন ফোনালাপ করেছেন।",
    "user_id": "667987fb293bcb6b67abf2d7"
}
```

Upon successful prediction, you will receive a JSON document that contains the inferred event `result` and the `summary` of your provided text.

```
{
    "result": "আন্তর্জাতিক",
    "summary": "যুক্তরাষ্ট্র ও জার্মানি দূরপাল্লার ক্ষেপণাস্ত্র মোতায়েনকে কেন্দ্র করে দুই দেশের মধ্যে সম্প্রতি উত্তেজনা বেড়ে গেছে।"
}
```

## License

This software is distributed and produced under the Apache License Version 2.0, January 2004. Please refer to the `LICENSE` file located in the root of this repository for more information.

## Team

- <a href="github.com/shafin-r">Shafin Rahman</a>
  - API developer
  - Database Administrator
  - Network Security Administrator
- Ayon Sen
  - ML Developer
  - Develops and maintains all of the models
