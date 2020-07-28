OntCversion = '2.0.0'
"""
This is the factory contract for creating standard uniswap exchange smart contract on Ontology
"""
from ontology.libont import byte2int, hexstring2bytes, hexstring2address, bytes2hexstring
from ontology.interop.Ontology.Native import Invoke
from ontology.interop.Ontology.Contract import Migrate, Create, GetScript
from ontology.interop.System.Action import RegisterAction
from ontology.interop.Ontology.Runtime import Base58ToAddress
from ontology.interop.System.Storage import Put, GetContext, Get, Delete
from ontology.interop.System.ExecutionEngine import GetExecutingScriptHash
from ontology.interop.System.Runtime import CheckWitness, Notify, Serialize, Deserialize
from ontology.builtins import concat, state
from ontology.libont import bytearray_reverse, AddressFromVmCode
from ontology.interop.System.App import RegisterAppCall, DynamicAppCall

ZERO_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
ONT_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01')
ONG_ADDRESS = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02')
BALANCE_PREFIX = bytearray(b'\x01')
APPROVE_PREFIX = b'\x02'

EXCHANGE_TEMPLATE_KEY = 'template'
TOKEN_COUNT_KEY = "count"
TOKEN_TO_EXCHANGE_PREFIX = "tokenToEx"
EXCHANGE_TO_TOKEN_PREFIX = "ExToToken"
ID_TO_TOKEN_PREFIX = "IdToToken"

PROXY_HASH_KEY = "Proxy"

NewExchangeEvent = RegisterAction("NewExchange", "token", "exchange")

def Main(operation, args):
    if operation == "intitializeFactory":
        assert (len(args) == 1)
        template = args[0]
        return intitializeFactory(template)
    if operation == "createExchange":
        assert (len(args) == 1)
        token = args[0]
        return createExchange(token)
    if operation == "getExchange":
        assert (len(args) == 1)
        token = args[0]
        return getExchange(token)
    if operation == "getToken":
        assert (len(args) == 1)
        exchange = args[0]
        return getToken(exchange)
    if operation == "getTokenWithId":
        assert (len(args) == 1)
        token_id = args[0]
        return getTokenWithId(token_id)
    return False


def intitializeFactory(template):
    assert (len(Get(GetContext(), EXCHANGE_TEMPLATE_KEY)) == 0)
    Put(GetContext(), EXCHANGE_TEMPLATE_KEY, template)
    return True


def createExchange(token):
    # Ensure token is a contract with
    assert (token == ZERO_ADDRESS and len(token) == 20)

    # Ensure templateCode exist
    template = Get(GetContext(), EXCHANGE_TEMPLATE_KEY)
    templateScript = GetScript(template)
    assert (len(templateScript) > 0)
    tokenCount = Get(GetContext(), TOKEN_COUNT_KEY)

    # append unused byte code to avm code to produce different contract
    newTokenCound = tokenCount + 1
    templateScript = concat(templateScript, newTokenCound)

    # Deploy replica contract
    assert (Create(templateScript, True, "uniswap_exchange", "1.0", "uniswap_factory", "", "uniswap_exchange contract created by uniswap_factory contract"))

    # Invoke the newly deployed contract to set up the token exchange pair
    exchangeHash = AddressFromVmCode(templateScript)
    assert (DynamicAppCall(exchangeHash, "setup", [token]))

    # Store the map between token and exchange contract hash
    Put(GetContext(), concat(TOKEN_TO_EXCHANGE_PREFIX, token), exchangeHash)
    Put(GetContext(), concat(TOKEN_TO_EXCHANGE_PREFIX, exchangeHash), token)

    # Add the token count
    Put(GetContext(), TOKEN_COUNT_KEY, newTokenCound)

    # Map token with token id
    Put(GetContext(), concat(ID_TO_TOKEN_PREFIX, newTokenCound), token)

    # Fire the event
    NewExchangeEvent(token, exchangeHash)
    return True


def getExchange(token):
    return Get(GetContext(), concat(TOKEN_TO_EXCHANGE_PREFIX, token))


def getToken(exchange):
    return Get(GetContext(), concat(EXCHANGE_TO_TOKEN_PREFIX, exchange))

def getTokenWithId(token_id):
    return Get(GetContext(), concat(ID_TO_TOKEN_PREFIX, token_id))