#include <tfhe/tfhe.h>
#include <tfhe/tfhe_io.h>
#include <stdio.h>
#include <iostream>

int main() {
    
    //reads the cloud key from file
    FILE* cloud_key = fopen("cloud.key","rb");
    TFheGateBootstrappingCloudKeySet* bk = new_tfheGateBootstrappingCloudKeySet_fromFile(cloud_key);
    fclose(cloud_key);
 
    //if necessary, the params are inside the key
    const TFheGateBootstrappingParameterSet* params = bk->params;

    //read the 2x16 ciphertexts
    LweSample* cipherin = new_gate_bootstrapping_ciphertext_array({{ input_width }}, params);
    LweSample* cipherout = new_gate_bootstrapping_ciphertext_array({{ output_width }}, params);
    LweSample* cipherwirein = new_gate_bootstrapping_ciphertext_array({{ wire_max }}, params);
    LweSample* cipherwireout = new_gate_bootstrapping_ciphertext_array({{ wire_max }}, params);

    //reads the 2x16 ciphertexts from the cloud file
    FILE* cloud_data = fopen("cloud.data","rb");
    for (int i=0; i<{{ input_width }}; i++) import_gate_bootstrapping_ciphertext_fromFile(cloud_data, &cipherin[i], params);
    fclose(cloud_data);

    //do some operations on the ciphertexts:
    {{% for stage in template_array %}}
    {{% for gate in stage %}}
    boots{{ gate[0] }}({{ gate[1] }},{{ gate[2] }},{{ gate[3] }},bk);
    {{% endfor %}}    
    {{% if not loop.last %}}std::swap(cipherwirein,cipherwireout);{{% endif %}}
    {{% endfor %}}

    //export the 32 ciphertexts to a file (for the cloud)
    FILE* answer_data = fopen("answer.data","wb");
    for (int i=0; i<{{ output_width }}; i++) export_gate_bootstrapping_ciphertext_toFile(answer_data, &cipherout[i], params);
    fclose(answer_data);

    //clean up all pointers
    delete_gate_bootstrapping_ciphertext_array({{ input_width }}, cipherin);
    delete_gate_bootstrapping_ciphertext_array({{ output_width }}, cipherout);
    delete_gate_bootstrapping_ciphertext_array({{ wire_max }}, cipherwirein);
    delete_gate_bootstrapping_ciphertext_array({{ wire_max }}, cipherwireout);
    delete_gate_bootstrapping_cloud_keyset(bk);

}