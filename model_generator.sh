# Bash script that generates python dataclasses based on a given json schema
# the json Schema are located in the "schemas" folder
# the script automatically generates the dataclasses in the "models" folder
# the script is called by the "generate_models.sh" script

#download the schemas zip folder from the github repo under following link:
link = 'https://git.scc.kit.edu/api/v4/projects/37573/jobs/artifacts/master/download?job=generate&file_type=archive'
# get environment variables ( in Bash!)



#download the zip file (this is a bash file!)
wget $link -O schemas.zip

#unzip the file
unzip schemas.zip

#delete the zip file
rm schemas.zip

# get the name of the schema files
SCHEMAS=$(ls schemas)

# for each schema file
for SCHEMA in $SCHEMAS
do
    # get the name of the schema file without the extension
    SCHEMA_NAME=$(echo $SCHEMA | cut -d'.' -f1)
    # generate the dataclass


    datamodel-codegen  --input schemas/$SCHEMA --input-file-type jsonschema --output models/$SCHEMA_NAME.py
    # open the file and change "Class Model" to "Class $SCHEMA_NAME"
    # save the file in the models folder
    sed -i "s/Class Model/Class $SCHEMA_NAME/g" models/$SCHEMA_NAME.py
done





# we have following pom.xml file and want a regex to read the version number

example="
    <modelVersion>4.0.0</modelVersion>

    <groupId>edu.kit.iai.webis</groupId>
    <artifactId>proof-models</artifactId>
    <version>1.0.3</version>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>"

# the regex is:
regex="version>([0-9]+.[0-9]+.[0-9]+)<"
[[ $example =~ $regex ]]