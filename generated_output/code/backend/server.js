const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const errorHandler = require('errorhandler');
const routes = require('./routes');

const app = express();
app.use(bodyParser.json());
app.use(cors());
app.use(errorHandler());
app.use('/tasks', routes);

app.listen(3000, () => console.log('Server running on port 3000'));