Cryptocurrency Exchange Ehell
=============================

## What is this?

CES is a command line interface to buy, sell and get information about crypto currencies.

The shell-like interface makes it easy to place orders, jump between different markets, see historic prices, etc. This uses [GNU readline](https://tiswww.case.edu/php/chet/readline/rltop.html) under the hood to provide parameter autocompletion and command history so performing any actions is quick and easy.

## Why would I use this?

I find it much simpler to type down a command than to have to click/scroll through an interface until I find what I need. For example, seeing the price fluctuation for the Ethereum/Stellar lumens market is as simple as this:

![](https://i.imgur.com/gLB9u3o.png)

Note that at any point you can press _TAB_ and that will display the list of possible terms/parameters to use next.

### Placing orders

When placing orders, there's some constants you can use to express quantities and rates at which you want to buy/sell. For example, if you wanted to sell all your Ethereum for Bitcoin but only when the price of BTC/ETH is 10% higher than the current sell price, you can do:

```
sell BTC ETH amount max rate ask * 1.1
```

This will implicitly:

* fetch your _ETH_ balance so it knows how much "max" is.
* fetch the current _ask_ price on the exchange you're using and multiply it by _1.1_ to gather the actual rate at which you want to sell.

Only after doing that and validating you have enough coins to perform the operation you'll be prompted to accept or cancel the operation.

### Help?

There's several commands available that allow you to either inspect coin/price related information or perform actions. For example, these are the ones available at the time of writing:

![](https://i.imgur.com/VNkIkbj.png)

## Which exchanges are supported?

Currently only [Bittrex](https://bittrex.com/) and [Binance](https://www.binance.com/) are supported but more can be easily added.

## Is this safe?

Let me start by saying **you should use it under your own risk**.

But yes, if you're concerned about something stealing your API keys then you shouldn't be as long as you trust the exchange wrappers used. This currently uses [python-bittrex](https://github.com/ericsomdahl/python-bittrex) and [python-binance](https://github.com/sammchardy/python-binance) to interact which each exchange's API, so there's nothing fishy. 

If you're concerned about your funds being lost in badly interpreted/typed transaction (e.g. selling Bitcoin for $100 when it's worth $1000), then be sure you can always review your actions. Whenever an order is about to be placed or a withdraw is about to be made, a confirmation dialog will show up and you'll need to explicitly type "yes" for the action to be carried out. e.g.

![](https://i.imgur.com/UEcANQe.png)

## Getting started

In order to get started, simply create a configuration file. If you clone the repo, keep in mind the `configs` directory is inside `.gitignore` so it's safe to place these files in there as they will never be committed into your repo.

### Configuration file

The configuration file has to be in [yaml](http://yaml.org/) format. A basic configuration file to use Bittrex would look like:

```yaml

exchanges:
    * name: bittrex
      api_key: 91220aacb69bc6401b1e04e290e022cd
      api_secret: 9c9e97f59eed930120633191a29bee5f
database:
    path: 'configs/config.db'
```

If you don't want to put your API keys in yet, you can simply set both fields to _null_. This will allow you to perform publicly accessible read operations like seeing order books, prices, etc.

The database path will be used to create a _sqlite3_ file to store some data. Currently only the address book is stored in it.

Note that you can set multiple exchange's keys, using different exchange names for them (e.g. "bittrex" and "binance"). If you specify multiple of them in your configuration file, you'll need to provide the one you want to use by using the `-e` parameter when running the shell.

#### Encrypting the configuration file

Given that the configuration file will contain your API keys, you may not want it to be stored in plain text on your filesystem. If that's the case, then you can use the `encrypter.py` script in the root of this project. This will encrypt your configuration file using AES in CFB mode and a passphrase you provide. Every time you run the shell, you'll have to provide the decryption key.

For example:

```bash
# This will encrypt the configs/config.yaml file and will emit the
# encrypted file into configs/config.yaml.encrypted
./encrypter.py -e -p configs/config.yaml  > configs/config.yaml.encrypted

# Now run the shell using -d (decrypt)
./shell.py -c configs/config.yaml.encrypted -d
```

### Running the application

In order to run the application, just execute:

```bash
./shell.py -c configs/config.yaml
```
