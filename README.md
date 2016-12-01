# ViettelPost Demo Web (Flask + MongoDB)

This is a demo web application (advanced) that connects to a MongoDB database named `ViettelPost`.
It provides:

- Dashboard (orders summary, COD total, chart)
- Track order page (show order and shipment history)
- PostOffices map (Leaflet)
- Shippers page (list + map)

## Requirements

- Python 3.10+
- MongoDB running locally on mongodb://localhost:27017 with a database named ViettelPost
- Data seeded for collections: users, orders, shipments, postoffices, shippers, transactions

## Install

pip install -r requirements.txt

## Run

python app.py
Open http://127.0.0.1:5000 in your browser.

## Notes

- The app uses CDN links for Bootstrap, Leaflet and Chart.js.
- Adjust MONGO_URI in app.py if your MongoDB is remote or protected.
