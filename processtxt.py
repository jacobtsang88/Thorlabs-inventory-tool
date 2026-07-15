#process the text, the headers will be encapsulated by stars, so use RegEx to figure that out
#output a json or python list/dict? maybe? 

class txt_to_list:
    def __init__(self):
        self.filename = "allproducts.txt"
    def convert(self):   
        with open (self.filename, "r") as file:
            productlist = []
            products = file.read().split()
            for i in products:
                productlist.append(i)
            return(productlist)