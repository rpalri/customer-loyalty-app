# Customer Loyalty App

## Description
Manufacturers and distributors of commodities commonly fail to connect to their end consumer. Although social media has helped them connect them with potential buyers and current users, they miss out on connecting the local dealers/retailers and hence fail to connect the entire set of stakeholders in the supply chain.
This app aims to fill this gap between the two. A manufacturer, or a distributor can use this app to communicate with their end consumer, while keeping their dealers in the loop. The manufacturer can direct loyalty points to the consumer via the retailer in the middle. This creates interest and additional business for the retailer and keeps the consumer engaged and committed for the added loyalty bonus they receive.

## Features
* Idependent registration of retailers
* Company provided retailer-code to keep a check on unverified registrations
* Mobile number verification on sign-up using OTP to ensure verified registrations
* Registration of consumers via retailers only to ensure retailer-interest
* Easy invoice upload via file or image capture
* Retailer live-dashboard includes customer level metrics
* Retailer has the ability to ask for redemption of customer's accrued loyalty points
* Dedicated customer live-dashboard with information on every purchase, total accrued points and status of gift disbursement
* Admin live-dashboard with retailer-level and customer-level data filters
* Approvals from admin integrated in the workflow
* Complete back-office workflow for the manufacturer/distributor
* Back-office roles include multiple levels: Operator, Checker, Manager and Admin
* Workflow management and user-wise permissions to add, edit and verify each data entry
* End-to-end workflow integration, does not require interaction with any other company apps/softwares/ERP etc.
* Simple one-time setup with flat learning curve

## Installation
1. Clone the directory or download on your computer
2. `cd` to the home directory of the project
3. Activate your virtual envirenment
4. run: ``` pip install -r requirements.txt ``` in your shell
5. Register for a free [Twillio Account](https://www.twilio.com/try-twilio) and note the following details in application.py:
    * account_sid: change line 23 in application.py
    * auth_token: change line 24 in application.py
    * temporary number: change line 25 in application.py
6. run: ``` flask run ``` to start the app in development mode for a demo on your local machine
7. You can also deploy on [heroku](www.heroku.com) referring to this [tutorial](https://devcenter.heroku.com/articles/getting-started-with-python)

## Testing
* visit [https://palri-customer-loyalty-app.herokuapp.com/login](https://palri-customer-loyalty-app.herokuapp.com/login)
* Note: registration might fail to work due to low funds in my Twillio trial account. If that is the case, use the following login details to explore the app:
   * Retailer/Trader username: "5" password: "a"
   * Customer/Plumber username: "123" password: "a"
* You can register as a retialer to start workflow
* Register a new customer (called plumber in this version)
* Add a new invoice for the registered customer
* login as operator with this as username and password: "123123"
* login as checker with this as uername and password: "456456"
* login as admin with this as username and password: "789789"

## Support
In case you find time to report any errors or bugs, you can write to me directly at rmpalri@gmail.com or visit [palrigraphy.com](palrigraphy.com/contact) to see others ways of connecting with me.
If you want to deploy this app for your company, write to me and we can discuss specifications to customise the web-app per your requirements.

## Roadmap
In future releases you might see:
* Workflow management toolkit in the admin dashboard
* Company profile settings in the admin dashboard
