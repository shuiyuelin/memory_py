# memory
chatbot powered by memory network

One Paragraph of project description goes here

## Tips
head data | awk 'BEGIN {FS="\t"}; {print $2}'

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you have to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags).

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc

```
{
  "sentence": "如何下载",
  "result": {
    "sentence": "如何下载",
    "score": 28.69175910949707,
    "timeout": -1,
    "answer": "请您扫描二维码，输入手机号和验证码，点击确认下载，苹果手机请到AppStore下载，安卓手机根据提示，点击用浏览器打开完成下载。",
    "sim": 0.9999999999999999,
    "from": "ML",
    "pre": "",
    "emotion": "null",
    "media": "下载",
    "class": "下载"
  },
  "user": "nlp.bank_psbc.request.user.string",
  "version": "0.1.0",
  "question": "如何下载"
}
```