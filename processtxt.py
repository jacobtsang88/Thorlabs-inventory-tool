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