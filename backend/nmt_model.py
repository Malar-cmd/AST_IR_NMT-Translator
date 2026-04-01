from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("Salesforce/codet5-base")


def translate_ir_with_nmt(ir_sequence):

    inputs = tokenizer(ir_sequence, return_tensors="pt", truncation=True)

    outputs = model.generate(**inputs, max_length=256)

    return tokenizer.decode(outputs[0], skip_special_tokens=True)