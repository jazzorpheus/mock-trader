# MockTrader

### Video Demo: https://youtu.be/uEFdlHU87Ik

### DISCLAIMER:

The implementation of many of the features of this web application formed part of a project for HarvardX's "CS50: Introduction to Computer Science" course. This means that some of the code here was written by instructors at Harvard and not by me. For example, most of the code in helpers.py and some of the code in application.py is by the instructors. However, with the exception of the /login and /logout routes, all of the routing in application.py as well as the corresponding HTML templates and their styling were coded by me.

### Description:

MockTrader is a web app that allows users to register for an account and manage a virtual portfolio of stocks. By default, new users will receive 10,000 USD in cash which they can then use to 'buy' stocks based upon live prices lifted directly from the IEX Exchange via the IEX Cloud API. Following the 'Quote' link takes users to a form where they can put in a company's unique stock symbol to obtain a quote for a single share in the company. To buy shares users must go to the 'Buy' page and enter the unique stock symbol of the company, E.g. NFLX for Netflix, followed by the number of shares they would like to purchase. They can also sell their shares in a similar manner following the 'Sell' link. The homepage/index provides a table with all shares currently owned by the user including their value based on current stock prices, plus a total net worth based on that plus their current cash. 'History' provides a complete history of transactions for the currently logged in user. Users can also add money via 'Add cash'.

### To Do:

    * Enable lookup() in helpers.py to access full company name
    * Prevent user from buying/selling 0 shares
