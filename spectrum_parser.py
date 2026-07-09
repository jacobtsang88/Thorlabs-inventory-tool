import re


class SpectrumParser:


    def parse(self, ws):

        header_row = self.find_header(ws)


        headers = self.build_headers(
            ws,
            header_row
        )


        columns = [
            self.classify(x)
            for x in headers
        ]


        return self.build_dictionary(
            ws,
            columns,
            header_row
        )


    def find_header(self, ws):

        for row in range(1,ws.max_row+1):

            text = ""

            for col in range(1,ws.max_column+1):

                value = ws.cell(row,col).value

                if value:
                    text += str(value).lower()


            if "wavelength" in text:
                return row


        return None



    def build_headers(self, ws, header_row):

        result=[]


        for col in range(1,ws.max_column+1):

            parts=[]

            for row in range(1,header_row+1):

                value = ws.cell(row,col).value

                if value:
                    parts.append(str(value))


            result.append(
                " ".join(parts)
            )


        return result



    def classify(self, header):

        product=None
        metric=None


        products = re.findall(
            r'[A-Z]{2}\d+[A-Z]\d+',
            header
        )


        if products:
            product=products[0]


        text=header.lower()


        if "reflectance" in text:
            metric="Reflectance"

        elif "transmission" in text:
            metric="Transmission"


        wavelength = (
            "wavelength" in text
        )


        return {
            "product":product,
            "metric":metric,
            "wavelength":wavelength
        }



    def build_dictionary(
        self,
        ws,
        columns,
        header_row
    ):

        spectra={}

        wavelength_col=None


        for i,c in enumerate(columns):

            if c["wavelength"]:
                wavelength_col=i


        for row in range(
            header_row+1,
            ws.max_row+1
        ):

            wavelength = ws.cell(
                row,
                wavelength_col+1
            ).value


            if wavelength is None:
                continue



            for col,c in enumerate(columns):

                if (
                    c["product"]
                    and
                    c["metric"]
                ):

                    value = ws.cell(
                        row,
                        col+1
                    ).value


                    if c["product"] not in spectra:
                        spectra[c["product"]]={}


                    if c["metric"] not in spectra[c["product"]]:
                        spectra[c["product"]][c["metric"]] = {}


                    spectra[c["product"]][c["metric"]][
                        float(wavelength)
                    ] = value


        return spectra