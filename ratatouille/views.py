from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TableInstance, Order, MenuItems, OrderId, Logging
import apiai
import json
from datetime import datetime, date

CLIENT_ACCESS_TOKEN = 'bf104e90c422496c8bb05a773ce997a4'


class State:
     new_order, menu_shown, processing, final, bill, close = range(6)


class CancelState:
    pending, done = range(2)


class Action:
    show_menu = 1
    add_order = 2
    item_info = 3
    cancel_confirmation = 4
    modify_order = 5
    show_caps = 6
    bill_order = 7
    close_order = 8
    generic = 9
    finalize_order = 10
    cancel_order = 11
    remove_item = 12
    remove_confirmation = 13
    recognition_prompt = 14

@csrf_exempt
def init(request):
    if request.method == "POST":
        if 'tbNo' in request.POST:
            tb_no = int(request.POST['tbNo'])  # get the table number
            orderid = OrderId()
            orderid.save()
            table = TableInstance(tableId=tb_no, state=State.new_order, orderId=orderid)  # insert into db
            table.save()
            response_frontend = dict()
            response_frontend['errorCode'] = 200
            response_frontend['message'] = "Table initialized"
            response_frontend['orderId'] = orderid.orderId
            return HttpResponse(json.dumps(response_frontend))
        else:
            return HttpResponse("Table number not sent")


@csrf_exempt
def index(request):
    return HttpResponse("Hello world! This is a response from the django app")
# Create your views here.


@csrf_exempt
def hit_me(request):
    if request.method == "POST":
        if 'name' in request.POST:
            name = request.POST['name']
            return HttpResponse("A post request was sent to the server" + name)
        else:
            return HttpResponse("Name not present in the request")
    if request.method == "GET":
        return HttpResponse("A get request was sent to the server")

def deep_search(needles, haystack):
    found = {}
    if type(needles)!=type([]):
        needles = [needles]
    if type(haystack)==type(dict()):
        for needle in needles:
            if needle in haystack.keys() and len(haystack[needle]) > 1:
                found[needle] = haystack[needle]
            elif len(haystack.keys()) > 0:
                for key in haystack.keys():
                    result = deep_search(needle, haystack[key])
                    if result:
                        for k, v in result.items():
                            found[k] = v
    elif type(haystack)==type([]):
        for node in haystack:
            result = deep_search(needles, node)
            if result:
                for k, v in result.items():
                    found[k] = v
    return found

count = 0
cancel_pending = False
@csrf_exempt
def listen(request):
    global count
    global cancel_pending
    if request.method == "POST":
        log = Logging()
        if 'reqText' in request.POST:
            req_text = request.POST['reqText']
        else:
            return HttpResponse("No reqText present")
        if 'orderId' in request.POST:
            order_id = int(request.POST['orderId'])
            current_table = TableInstance.objects.filter(orderId__orderId=order_id).first()
        else:
            return HttpResponse('No order id present')
        if req_text is not None and req_text is not '':
            log.asr_text = str(req_text)
            log.asr_time = date.strftime(datetime.now(),"%d/%m/%Y-%H:%M:%S")
            ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
            request_ai = ai.text_request()
            request_ai.session_id = "1"
            request_ai.query = req_text
            response_ai = request_ai.getresponse()
            str_resp = response_ai.read()
            resp_json = json.loads(str_resp)
            action = int(resp_json['result']['action'])
            log.nlu_text = str(resp_json['result']['resolvedQuery'])
            log.nlu_time = date.strftime(datetime.now(),"%d/%m/%Y-%H:%M:%S")
            log.action = action
            print "Action: " + str(action)
            if action == Action.show_menu:
                count = 0
                response_frontend = dict()
                dish_info = []
                tags = None
                if resp_json['result']['parameters']['dishtag'] is not None:
                    tags = resp_json['result']['parameters']['dishtag']
                if tags is not None and len(tags) > 0:
                    mItems = MenuItems.objects.all()
                    for mi in mItems:
                        for tag in tags:
                            if tag in mi.tags:
                                dish_info.append(mi.name)
                    current_table.state = State.menu_shown
                    current_table.save()
                    response_frontend['errorCode'] = 200
                    response_frontend['pre'] = Action.show_menu
                    response_frontend['message'] = dish_info
                    print "Server response ingredient case: " + str(response_frontend)
                    log.errorCode = 200
                    log.pre = Action.show_menu
                    log.save()
                    return HttpResponse(json.dumps(response_frontend))
                else:
                    mItems = MenuItems.objects.all()
                    for mi in mItems:
                        dish_info.append(mi.name)
                    current_table.state = State.menu_shown
                    current_table.save()
                    response_frontend['errorCode'] = 200
                    response_frontend['pre'] = Action.show_menu
                    response_frontend['message'] = dish_info
                    print "Server response normal case: " + str(response_frontend)
                    log.errorCode = 200
                    log.pre = Action.show_menu
                    log.save()
                    return HttpResponse(json.dumps(response_frontend))
            elif action == Action.add_order:
                count = 0
                response_frontend = dict()
                dict_items = {}
                params = resp_json['result']['parameters']
                response_frontend['errorCode'] = 400
                response_frontend['message'] = 'Sorry, I didn\'t get that'
                name = None
                for item_detail in params['item_qty']:
                    if 'item' in item_detail:
                        name = item_detail['item']
                        quantity = 1
                    if 'quantity' in item_detail:
                        try:
                            quantity = int(item_detail['quantity'])
                        except:
                            quantity = 1
                    if name is not None:
                        order_list = Order.objects.filter(name=name, orderId__orderId=current_table.orderId.orderId)
                        if order_list is not None and len(order_list) > 0:
                            order = order_list.first()
                            order.quantity = order.quantity + quantity
                            order.save()
                            current_table.state = State.processing
                            current_table.save()
                            dict_items[str(name)] = order.quantity
                            response_frontend['errorCode'] = 200
                        else:
                            new_order = Order()
                            new_order.name = name
                            orderId_recv = OrderId.objects.get(orderId=current_table.orderId.orderId)
                            new_order.orderId = orderId_recv
                            new_order.quantity = quantity
                            dict_items[str(name)] = quantity
                            new_order.orderId.orderId = current_table.orderId.orderId
                            new_order.save()
                            current_table.state = State.processing
                            current_table.save()
                            response_frontend['errorCode'] = 200
                response_frontend['message'] = dict_items
                response_frontend['pre'] = Action.add_order
                print "Server response: " + str(response_frontend)
                log.errorCode = 200
                log.pre = Action.add_order
                log.save()
                return HttpResponse(json.dumps(response_frontend))
            elif action == Action.item_info:
                count = 0
                response_frontend = dict()
                params = resp_json['result']['parameters']
                items_info_name = params['item']
                if items_info_name is not None:
                    mi = MenuItems.objects.filter(name=items_info_name).first()
                    if mi is not None:
                        dict_sets = dict()
                        dict_sets[mi.name] = mi.description
                        response_frontend['errorCode'] = 200
                        response_frontend['pre'] = Action.item_info
                        response_frontend['message'] = dict_sets
                        print "Server response: " + str(response_frontend)
                        log.errorCode = 200
                        log.pre = Action.item_info
                        log.save()
                        return HttpResponse(json.dumps(response_frontend))
                    else:
                        response_frontend['errorCode'] = 400
                        response_frontend['message'] = 'Not available in the menu'
                        print "Server response: " + str(response_frontend)
                        log.errorCode = 400
                        log.save()
                        return HttpResponse(json.dumps(response_frontend))
                else:
                    #TODO: Change error codes to specific codes for cases
                    response_frontend['errorCode'] = 400
                    response_frontend['message'] = 'Not recognised'
                    print "Server response: " + str(response_frontend)
                    log.errorCode = 400
                    log.save()
                    return HttpResponse(json.dumps(response_frontend))
            elif action == Action.cancel_confirmation:
                current_table.cancel = True
                current_table.save()
                count = 0
                response_frontend = dict()
                response_frontend['errorCode'] = 200
                response_frontend['pre'] = Action.cancel_confirmation
                print "Server response: " + str(response_frontend)
                log.errorCode = 200
                log.pre = Action.cancel_confirmation
                log.save()
                return HttpResponse(json.dumps(response_frontend))
            elif action == Action.finalize_order:
                count = 0
                response_frontend = dict()
                current_table.state = State.final
                current_table.save()
                response_frontend['errorCode'] = 200
                response_frontend['pre'] = Action.finalize_order
                response_frontend['message'] = 'Order finalized'
                print "Server response: " + str(response_frontend)
                log.errorCode = 200
                log.pre = Action.finalize_order
                log.save()
                return HttpResponse(json.dumps(response_frontend))
            elif action == Action.show_caps:
                count = 0
                response_frontend = dict()
                response_frontend['errorCode'] = 200
                response_frontend['pre'] = Action.show_caps
                response_frontend['message'] = 'Greet'
                print "Server response: " + str(response_frontend)
                log.errorCode = 200
                log.pre = Action.show_caps
                log.save()
                return HttpResponse(json.dumps(response_frontend))
            elif action == Action.cancel_order:
                count = 0
                confval = int(resp_json['result']['parameters']['confval'])
                if confval == 1000:
                    current_table.state = State.close
                    current_table.save()
                    response_frontend = dict()
                    response_frontend['errorCode'] = 200
                    response_frontend['pre'] = Action.cancel_order
                    response_frontend['message'] = confval
                    print "Server response: " + str(response_frontend)
                    log.errorCode = 200
                    log.pre = Action.cancel_order
                    log.save()
                    return HttpResponse(json.dumps(response_frontend))
                elif confval == 1001:
                    response_frontend = dict()
                    response_frontend['errorCode'] = 200
                    response_frontend['pre'] = Action.cancel_order
                    response_frontend['message'] = confval
                    print "Server response: " + str(response_frontend)
                    log.errorCode = 200
                    log.pre = Action.cancel_order
                    log.save()
                    return HttpResponse(json.dumps(response_frontend))
            elif action == Action.remove_item:
                count = 0
                response_frontend = dict()
                item_name = deep_search(["item"], resp_json)["item"]
                try:
                    order = Order.objects.get(orderId__orderId=current_table.orderId.orderId, name=item_name)
                except:
                    response_frontend['errorCode'] = 200
                    response_frontend['pre'] = Action.remove_item
                    response_frontend['message'] = 'Sorry I could not find ' + item_name + ' in your order.'
                    print "Server response: " + str(response_frontend)
                    log.errorCode = 200
                    log.pre = Action.remove_item
                    log.save()
                response_frontend['errorCode'] = 200
                response_frontend['pre'] = Action.remove_item
                response_frontend['message'] = 'Are you sure you want to remove ' + item_name + '?'
                print "Server response: " + str(response_frontend)
                log.errorCode = 200
                log.pre = Action.remove_item
                log.save()
                return HttpResponse(json.dumps(response_frontend))
            elif action == Action.remove_confirmation:
                if current_table.cancel:
                    current_table.cancel = False
                    current_table.save()
                    count = 0
                    confval = int(resp_json['result']['parameters']['confval'])
                    if confval == 1000:
                        current_table.state = State.close
                        current_table.save()
                        response_frontend = dict()
                        response_frontend['errorCode'] = 200
                        response_frontend['pre'] = Action.cancel_order
                        response_frontend['message'] = confval
                        print "Server response: " + str(response_frontend)
                        log.errorCode = 200
                        log.pre = Action.cancel_order
                        log.save()
                        return HttpResponse(json.dumps(response_frontend))
                    elif confval == 1001:
                        response_frontend = dict()
                        response_frontend['errorCode'] = 200
                        response_frontend['pre'] = Action.cancel_order
                        response_frontend['message'] = confval
                        print "Server response: " + str(response_frontend)
                        log.errorCode = 200
                        log.pre = Action.cancel_order
                        log.save()
                        return HttpResponse(json.dumps(response_frontend))
                count = 0
                response_frontend = dict()
                confval = int(resp_json['result']['parameters']['confval'])
                if confval == 1000:
                    item_name = deep_search(["item"], resp_json)["item"]
                    try:
                        order = Order.objects.get(orderId__orderId=current_table.orderId.orderId, name=item_name)
                        order.delete()
                    except:
                        response_frontend['errorCode'] = 200
                        response_frontend['pre'] = Action.remove_item
                        response_frontend['message'] = 'Sorry I could not find ' + item_name + ' in your order.'
                        print "Server response: " + str(response_frontend)
                        log.errorCode = 200
                        log.pre = Action.remove_item
                        log.save()
                        return HttpResponse(json.dumps(response_frontend))
                    response_frontend['errorCode'] = 200
                    response_frontend['pre'] = Action.remove_confirmation
                    response_frontend['message'] = item_name
                    print "Server response: " + str(response_frontend)
                    log.errorCode = 200
                    log.pre = Action.remove_confirmation
                    log.save()
                    return HttpResponse(json.dumps(response_frontend))
                else:
                    response_frontend['errorCode'] = 200
                    response_frontend['pre'] = Action.remove_confirmation
                    response_frontend['message'] = -1
                    print "Server response: " + str(response_frontend)
                    log.errorCode = 200
                    log.pre = Action.remove_confirmation
                    log.save()
                    return HttpResponse(json.dumps(response_frontend))
            elif action == Action.generic:
                count = 0
                response_frontend = dict()
                response_frontend['errorCode'] = 200
                response_frontend['pre'] = Action.generic
                response_frontend['message'] = resp_json['result']['parameters']['req_item']
                print "Server response: " + str(response_frontend)
                log.errorCode = 200
                log.pre = Action.generic
                log.save()
                return HttpResponse(json.dumps(response_frontend))
            elif action == Action.modify_order:
                count = 0
                response_frontend = dict()
                dict_items = {}
                confval = int(resp_json['result']['parameters']['opcode'])
                print "Confval: " + str(confval)
                item_name = deep_search(["item"], resp_json)["item"]
                print "Quantity: " + resp_json['result']['parameters']['qty']
                try:
                    quantity = int(resp_json['result']['parameters']['qty'])
                except:
                    response_frontend['errorCode'] = 400
                    response_frontend['message'] = 'Sorry, I didn\'t get that'
                    print "Server response: " + str(response_frontend)
                    log.errorCode = 400
                    log.save()
                    return HttpResponse(json.dumps(response_frontend))
                order = Order.objects.get(orderId__orderId=current_table.orderId.orderId, name=item_name)
                if confval == 10000:
                    order.quantity = quantity
                    order.save()
                elif confval == 10001:
                    order.quantity += quantity
                    order.save()
                elif confval == 10002:
                    if order.quantity - quantity > 0:
                        order.quantity -= quantity
                        order.save()
                    else:
                        response_frontend['errorCode'] = 400
                        response_frontend['pre'] = Action.modify_order
                        response_frontend['message'] = 'Sorry, I didn\'t get that'
                        print "Server response: " + str(response_frontend)
                        log.errorCode = 400
                        log.save()
                        return HttpResponse(json.dumps(response_frontend))
                order_list = Order.objects.filter(orderId__orderId=current_table.orderId.orderId)
                for a in order_list:
                    print str(a.name), str(a.quantity)
                    dict_items[str(a.name)] = a.quantity
                response_frontend['errorCode'] = 200
                response_frontend['pre'] = Action.modify_order
                response_frontend['message'] = dict_items
                print "Server response: " + str(response_frontend)
                log.errorCode = 200
                log.pre = Action.modify_order
                log.save()
                return HttpResponse(json.dumps(response_frontend))
            else:
                response_frontend = dict()
                if action == -100:
                    count += 1
                    if count % 2 == 0:
                        log.count = count
                        count = 0
                        if current_table is not None:
                            if current_table.state == State.new_order:
                                response_frontend['errorCode'] = 200
                                response_frontend['pre'] = Action.recognition_prompt
                                response_frontend['message'] = "Please say Menu to see the Menu"
                                print "Server response: " + str(response_frontend)
                                log.errorCode = 200
                                log.pre = Action.recognition_prompt
                                log.save()
                                return HttpResponse(json.dumps(response_frontend))
                            elif current_table.state == State.menu_shown or current_table.state == State.processing:
                                response_frontend['errorCode'] = 200
                                response_frontend['pre'] = Action.recognition_prompt
                                response_frontend['message'] = "To order please say the dish name"
                                print "Server response: " + str(response_frontend)
                                log.errorCode = 200
                                log.pre = Action.recognition_prompt
                                log.save()
                                return HttpResponse(json.dumps(response_frontend))
                response_frontend = dict()
                response_frontend['errorCode'] = 400
                response_frontend['message'] = 'Sorry, I didn\'t get that'
                print "Server response: " + str(response_frontend)
                log.errorCode = 400
                log.save()
                return HttpResponse(json.dumps(response_frontend))
        else:
            print "Server response: req_text is none"
            return HttpResponse("req_text is none")
    print "Server response: What the hell did you send?"
    return HttpResponse("What the hell did you send?")
