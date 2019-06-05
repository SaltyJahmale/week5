def repeating_key_xor(message_in_bytes, key):

    output_bytes = b''
    index = 0

    for byte in message_in_bytes:
        output_bytes += bytes([byte ^ key[index]])
        if(index + 1) == len(key):
            index = 0
        else:
            index += 1
    return output_bytes

def main():
    message = b"Burning 'em, if you ain't quick and nimble " \
              b"I go crazy when I hear a cymbal"
    key = b"ICE"
    ciphertext = repeating_key_xor(message, key)
    print(ciphertext.hex())

if __name__ == '__main__':
    main()