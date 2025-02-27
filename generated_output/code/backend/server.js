const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const errorhandler = require('errorhandler');
const jwt = require('express-jwt');
const routes = require('./routes');

const app = express();

app.use(bodyParser.json());
app.use(cors());
app.use(errorhandler());
app.use(jwt({ secret: 'your_secret_key' }));

app.use('/tasks', routes);

app.listen(3000, () => console.log('Server running on port 3000'));