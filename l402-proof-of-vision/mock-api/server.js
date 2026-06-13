const express = require('express');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');
const fs = require('fs');

const app = express();
const port = 3000;

// Setup connection to LND
const lndHost = 'lnd:10009';
const lndDataPath = '/root/.lnd';
const tlsCertPath = path.join(lndDataPath, 'tls.cert');
const macaroonPath = path.join(lndDataPath, 'data', 'chain', 'bitcoin', 'regtest', 'admin.macaroon');

const tlsCert = fs.readFileSync(tlsCertPath);
const macaroon = fs.readFileSync(macaroonPath).toString('hex');

const sslCreds = grpc.credentials.createSsl(tlsCert);
const macaroonCreds = grpc.credentials.createFromMetadataGenerator((_args, callback) => {
    let metadata = new grpc.Metadata();
    metadata.add('macaroon', macaroon);
    callback(null, metadata);
});
const credentials = grpc.credentials.combineChannelCredentials(sslCreds, macaroonCreds);

const protoDir = path.join(__dirname, 'protos');
const packageDefinition = protoLoader.loadSync(
    path.join(protoDir, 'lightning.proto'),
    {
        keepCase: true,
        longs: String,
        enums: String,
        defaults: true,
        oneofs: true,
        includeDirs: [protoDir]
    }
);
const lnrpc = grpc.loadPackageDefinition(packageDefinition).lnrpc;
const lightning = new lnrpc.Lightning(lndHost, credentials);

function createInvoice() {
    return new Promise((resolve, reject) => {
        lightning.addInvoice({ value: '1000' }, (err, response) => {
            if (err) {
                console.error('Error creating invoice:', err);
                return reject(err);
            }
            console.log('Successfully created invoice');
            resolve(response);
        });
    });
}

app.get('/sun_sign', async (req, res) => {
    console.log(`Request received for /sun_sign`);
    try {
        const invoiceResponse = await createInvoice();
        const token = invoiceResponse.r_hash.toString('hex');
        const invoice = invoiceResponse.payment_request;
        const l402Header = `L402 token="${token}", invoice="${invoice}"`;
        
        res.set('WWW-Authenticate', l402Header);
        return res.status(402).send('Payment Required');
    } catch (err) {
        return res.status(500).send('Error communicating with LND.');
    }
});

app.listen(port, () => {
    console.log(`Mock API with REAL LND integration starting on port ${port}`);
    lightning.getInfo({}, (err, response) => {
        if (err) {
            return console.error('Failed to get info from LND:', err);
        }
        console.log('Successfully connected to LND (getInfo):', response.identity_pubkey);
    });
});
