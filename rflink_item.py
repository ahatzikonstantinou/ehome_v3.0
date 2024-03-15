import web

# Define URLs
urls = (
    '/rflink_item', 'RFLinkItemIndex',
    '/rflink_item/create', 'RFLinkItemCreate',
    '/rflink_item/update/(\d+)', 'RFLinkItemUpdate',
    '/rflink_item/delete/(\d+)', 'RFLinkItemDelete'
)

# Initialize app with URLs
app = web.application(urls, globals())

# Define global render
render = web.template.render('templates/')

# Mock database (replace this with actual database)
items = []

# Define classes for different routes
class RFLinkItemIndex:
    def GET(self):
        return render.index(items)

class RFLinkItemCreate:
    def POST(self):
        data = web.input()
        items.append(data.item)
        raise web.seeother('/')

class RFLinkItemUpdate:
    def GET(self, item_id):
        item_id = int(item_id)
        return render.update(items[item_id])

    def POST(self, item_id):
        item_id = int(item_id)
        data = web.input()
        items[item_id] = data.item
        raise web.seeother('/')

class RFLinkItemDelete:
    def POST(self, item_id):
        item_id = int(item_id)
        del items[item_id]
        raise web.seeother('/')

app_rflink_items = web.application(urls, locals())
