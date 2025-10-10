'''
https://amphibiaweb.org/api/ws.html

1, 2 in ref sheet = 0, 1 in our sheet

'''

import os
import openai
from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
from egg_analysis import get_url, get_xml
import time

load_dotenv()

# Send prompt to LLM to classify reproductive style and return confidence score
def query_reproductive_style(text):

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = (
        "Extract and return only the reproductive style (where the species lays its eggs) from the following text. "
        "Only respond with ONE WORD: '0' for aquatic reproductive style, '1' for terrestrial reproductive style, "
        "and '2' for live-bearing frogs (live birth instead of eggs). Eggs laid in water bodies such as streams, rivers, "
        "lakes, or isolated ponds are considered aquatic ('0'). Eggs laid NEAR but not IN water (such as on land, "
        "in burrows, under rocks, or in leaf litter) are considered terrestrial ('1'). If males or females carry the eggs "
        "after they are laid, classify them based on where the eggs were originally deposited. Do not base classification "
        "on where the larvae develop. After your classification, include a comma followed by your confidence in the classification "
        "on a scale from 0 to 100. A higher number means the classification was clearly and explicitly stated in the text; a lower "
        "number means it was inferred or unclear. Respond with the classification and the confidence number only, separated by a comma. "
        "Do not include any units or explanation.\n\n"
        f"Text: {text}\n\n"
        "Response:"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=10
    )
    
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    # Load frog dataset to augment with reproductive style and confidence
    results_spreadsheet = "01_frog_data_compilation/results/froggy_analysis_results.csv"
    df_all = pd.read_csv(results_spreadsheet)

    df_all["Egg Style"] = None
    egg_style_confidence_df = pd.DataFrame(columns=["Name", "Egg Style", "Confidence"])

    # Loop through each species and retrieve XML + LLM classification
    for i, row in df_all.iterrows():

        genus, species = row["Name"].split(' ')

        while True:
            print(f"Processing {i}: {genus} {species}")

            try:

                url = get_url(genus, species)
                xml_data = get_xml(url)

                if xml_data and "NONEXISTENT PAGE" not in xml_data:
                    result = query_reproductive_style(xml_data)
                    if "," in result:
                        egg_style, confidence = result.split(",")
                        egg_style = egg_style.strip()
                        confidence = confidence.strip()
                    else:
                        egg_style, confidence = "-", "-"
                else:
                    egg_style, confidence = "-", "-"

                df_all.at[i, "Egg Style"] = egg_style
                egg_style_confidence_df.loc[len(egg_style_confidence_df)] = [row["Name"], egg_style, confidence]

                # Auto-save every 100 entries
                if i % 100 == 0 and i != 0:
                    print(f"Auto-saving confidence data at row {i}")
                    egg_style_confidence_df.to_csv("01_frog_data_compilation/results/egg_style_confidence.csv", index=False)
                
                break # Exit retry loop on success

            # Handle OpenAI rate limits with wait-and-retry
            except openai.RateLimitError:
                print("Rate limit hit. Trying again in 5 seconds")
                time.sleep(5)
                continue  # retry same row

            # Handle billing or quota-related errors
            except openai.AuthenticationError as e:
                if "billing" in str(e).lower() or "insufficient_quota" in str(e).lower():
                    print("Billing error: saving progress and exiting.")
                    egg_style_confidence_df.to_csv("01_frog_data_compilation/results/egg_style_confidence.csv", index=False)
                    df_all.to_csv("01_frog_data_compilation/results/froggy_analysis_results.csv", index=False)
                    exit() # end program
                else:
                    raise

    # Save final results after loop completion
    egg_style_confidence_df.to_csv("01_frog_data_compilation/results/egg_style_confidence.csv", index=False)
    df_all.to_csv("01_frog_data_compilation/results/froggy_analysis_results.csv", index=False)
    print("All results saved successfully.")