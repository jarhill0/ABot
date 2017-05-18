import wolframalpha

wolframalphaClient = wolframalpha.Client("GG48T9-HA9P3QKQAU")


def query_wa(args):
    a = wolframalphaClient.query(" ".join(args))
    array = []
    for pod in a.pods:
        if pod.text is not None:
            string = ""
            string += "*" + pod.title + "*\n"
            string += pod.text
            array.append(string)
    m = "\n\n".join(array)
    if not m:
        return "Error processing input"
    return m
