# Sportowe Świry

Web application for creating sports challenges, available [here](https://sportoweswiry.com.pl/).


## Table of Contents
* [General Info](#general-information)
* [Technologies Used](#technologies-used)
* [Features](#features)
* [Setup](#setup)
* [Project Status](#project-status)
* [Contributing](#contributing)
* [Sources](#sources)
* [Contact](#contact)
* [License](#license)


## General Information
Sportowe Świry web application is used to compete and have fun with a group of your friends as part of sports challenges. The purpose of this app is motivate for regular training and taking care of your fitness and health. The main functionalities of the application:

* Creating challenges that match the capabilities of participants
* Setting the distance that you will be competing in your physical activities each week. Each week of the challenge can have a different goal. Failure to achieve the goal involves the need to buy a prize for more diligent participants
* Possibility of competition for supporters of various types of activities, thanks to the system of coefficients that calculates the distances covered
* Presentation of physical activity statistics, allowing you to track your progress

The backend of the application was created using the Python language and the Flask framework.

![image](https://user-images.githubusercontent.com/98742733/219953392-34f2cfa1-378a-4eb5-b783-440ab6df9937.png)


## Technologies Used
* Framework Python-Flask
* Jinja templates
* SQLAlchemy (MySQL)
* Pandas
* Bootstrap
* CSS
* HTML
* Git


## Features
The most important functionalities of the application:

* Saving your activities in the database. Keeping statistics and visual presentation of your achievements
* Login and authorization via Google and Facebook accounts
* Possibility to create your own sports challenges (public or private)
* Opportunity sync your activities with Strava account
* Automatic emails with information about the status of your challenges, completed weeks and other important information
* Built-in mailbox

Full instruction for application [here](https://sportoweswiry.com.pl/instrukcja).

![image](https://user-images.githubusercontent.com/98742733/219950315-6d70a4e0-321e-4d5d-8975-deaab2d51cbd.png)


## Setup

* Clone repository
* Rename `.env.example` to `.env` and set your values:

```
SECRET_KEY=SomeRandomString
SQLALCHEMY_DATABASE_URI=mysql://<db_user>:<db_password>@<db_host>/<db_name>

MAIL_SERVER=<example.com>
MAIL_PORT=<port_number>
MAIL_USERNAME=<admin@example.com>
MAIL_PASSWORD=<password>
MAIL_DEFAULT_SENDER=<admin@example.com>

FB_CLIENT_ID=<fb_client_id>
FB_CLIENT_SECRET=<fb_client_secret>
GOOGLE_CLIENT_ID=<google_client_id>
GOOGLE_PROJECT_ID=<google_project_id>
CLIENT_SECRET=<google_client_secret>
```

* Create a virtual environment
```
python -m venv venv
```
* Install packages from `requirements.txt`
```
pip install -r requirements.txt
```
* Run command
```
flask run
```


## Project Status

The project is now complete and available for public use. 
In the future, the application will be developed in terms of:

* Optimization of operation
* Refinement of the graphical interface

Demo account in the application:
* login: PytDev
* password: 12345678

## Contributing
Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

Fork the Project
* Create your Feature Branch (git checkout -b feature/AmazingFeature)
* Commit your Changes (git commit -m 'Add some AmazingFeature')
* Push to the Branch (git push origin feature/AmazingFeature)
* Open a Pull Request

## Sources
We created applications as part of learning programming and building a portfolio.
Fundamentals of developing web applications in Flask was based on [this tutorial.](https://www.udemy.com/course/python-flask-aplikacje-webowe/)

## Contact
App created by [@LukBartsch](https://github.com/LukBartsch) 

[![LinkedIn][github-shield]][github-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

and [@MaBober](https://github.com/MaBober)

[![LinkedIn][github-shield]][github-bober-url]
[![LinkedIn][linkedin-shield]][linkedin-bober-url]

Feel free to contact us!


## License
This project is open source and available under the MIT License.


[github-shield]: https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white
[github-url]: https://github.com/LukBartsch
[github-bober-url]: https://github.com/MaBober
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/lukasz-bartsch/
[linkedin-bober-url]: https://www.linkedin.com/in/marcinbober/




