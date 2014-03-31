# mammoth

Project mammoth is a driver to orchestrate load testing on Marathon/Mesos, with current implementation tailored towards launching Jenkins.

## Installation

Dependencies:
* Python 2.7+
* VirtualEnv

To install mammoth, please follow the steps below:
```
$ git clone https://github.com/mohitsoni/mammoth/
$ cd mammoth
$ virtualenv --no-site-packages venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## Usage

With mammoth setup now, let's quickly launch a hello-world job on mammoth. But before we can do that, we need to update ```driver.cfg``` file to provide marathon endpoint. Once that's updated, please execute following command:

```
$ python main.py start hellojob
```

## Fixtures

Mammoth works with fixtures. At mammoth root, you'll find a ```fixtures``` directory. It has following structure:
* fixtures/
  * apps/ # List of payloads, that can be used for creating app in marathon.
  * jobs/ # List of payloads, that can be used submitted to a created app.

