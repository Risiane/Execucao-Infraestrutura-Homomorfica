import os
import boto3
import tenseal as ts

ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localstack:4566")
BUCKET = os.getenv("BUCKET_NAME", "he-bucket")

def s3_client():
    # Cliente S3 apontando para o LocalStack.
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1"
    )

def get_object_bytes(s3, key):
    # Baixa um objeto do bucket.
    response = s3.get_object(Bucket=BUCKET, Key=key)
    return response["Body"].read()

def main():
    print("[SERVIDOR] Verificação de segurança iniciada.")

    secret_path = "/tmp/he_secret_context.tenseal"

    # O servidor não deve possuir o contexto secreto.
    if os.path.exists(secret_path):
        print("[ALERTA] Chave secreta encontrada no servidor. Isso NÃO deveria acontecer.")
    else:
        print("[OK] Chave secreta não existe no servidor.")

    s3 = s3_client()

    # O servidor carrega apenas o contexto público.
    public_context_bytes = get_object_bytes(s3, "context/public_context.tenseal")
    public_context = ts.context_from(public_context_bytes)

    # Baixa um resultado criptografado.
    encrypted_result_bytes = get_object_bytes(
        s3,
        "result/Norte_soma_criptografada.tenseal"
    )

    encrypted_result = ts.bfv_vector_from(public_context, encrypted_result_bytes)

    # Tentativa de descriptografia sem chave secreta.
    # O comportamento esperado é falhar.
    try:
        decrypted = encrypted_result.decrypt()
        print("[ALERTA] O servidor conseguiu descriptografar:", decrypted)
    except Exception as error:
        print("[OK] O servidor não conseguiu descriptografar o resultado.")
        print("[MOTIVO] Contexto público não possui chave secreta.")
        print("[ERRO ESPERADO]", str(error))

    print("[SERVIDOR] Verificação de segurança finalizada.")

if __name__ == "__main__":
    main()
