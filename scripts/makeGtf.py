from argparse import ArgumentParser
import re
import gzip

#get the orfs, function and taxonomy annotations from command line
parser = ArgumentParser()
parser.add_argument("--orfs", dest="orfs", help="fasta containing ORF sequences from prodigal")
parser.add_argument("--functions", dest="funs", help="eggnog-mapper output functions")
parser.add_argument("--taxonomy", dest="taxa", help="MEGAN blast2lca assigned taxonomy")
parser.add_argument("--output", dest="outfile", help="Output filename")
parser.add_argument("--output-short", dest="shortout", help="Output filename for short GTF (only gene_id in 9th col)")
args = parser.parse_args()

#open the files
orfs = gzip.open(args.orfs,'rt')
funs = gzip.open(args.funs,'rt')
taxa = gzip.open(args.taxa,'rt')
outfile = open(args.outfile,'w')
shortout = open(args.shortout,'w')

#dictionary to store the open reading frames
orfdic = {}
orfannotdic = {}
annotlist = []

#fill dictionary with mappings from prodigal
for i in orfs:
    if i[0] == ">":
        entry = i.strip("\n").split()
        orfname = entry[0].strip(">")
        contigname = re.sub("_[0-9]*$","",orfname)
        start = entry[2]
        end = entry[4]
        direction = entry[6]
        if direction == "1":
            direction = "+"
        else:
            direction = "-"
        orfdic[orfname] = {"con":contigname, "s":start, "e":end, "d":direction}
        orfannotdic[orfname] = {}
orfs.close()

#add functional annotations to orf dictionary
funheader=["query_name","seed_eggNOG_ortholog","seed_ortholog_evalue","seed_ortholog_score","Predicted_taxonomic_group","Predicted_protein_name","Gene_Ontology_terms","EC_number","KEGG_ko","KEGG_Pathway","KEGG_Module","KEGG_Reaction","KEGG_rclass","BRITE","KEGG_TC","CAZy","BiGG_Reaction","tax_scope","eggNOG_OGs","bestOG","COG_Functional_Category","eggNOG_free_text_description"]

for i in funs:
    if i[0] == "#":
            pass
    else:
        entry = i.strip("\n").split("\t")
        orfname = entry[0]
        for j in range(len(entry)):
            if j == 0:
                pass
            else:
                entry[j]=entry[j].replace(" ","")
                if funheader[j]=="COG_Functional_Category":
                    entry[j]=",".join(list(entry[j]))
                if funheader[j]=="KEGG_Pathway" and entry[j] != "":
                    listed=entry[j].split(",")
                    entry[j]=",".join([x for x in listed if x[0:3]=="map"])
                #manually extract COGs from eggnog mapper OG list
                if funheader[j]=="eggNOG_OGs" and entry[j] != "":
                    listed=entry[j].split(",")
                    cogs=[]
                    for k in listed:
                        if k[0:3] == "COG":
                            if k.split("@")[0] not in cogs:
                                cogs.append(k.split("@")[0])
                    orfannotdic[orfname]["COGs"] = ",".join(cogs)
                orfannotdic[orfname][funheader[j]] = entry[j]

annotlist =  funheader[1:]
annotlist.append("COGs")
taxlist = ["kingdom","phylum","class","order","family","genus","species"]
for j in taxlist:
       annotlist.append(j)

#add taxonomic annotations to orf dictionary
for i in taxa:
    entry = i.strip("\n").split(";")
    orfname = entry[0]
    if len(entry) >= 4:
        kingdom = entry[2]
    else:
        kingdom = "k__unassigned"
    if len(entry) >= 6:
        phylum = kingdom+"|"+entry[4]
    else:
        phylum = kingdom+"|"+"p__unassigned"
    if len(entry) >= 8:
        clas = phylum+"|"+entry[6]
    else:
        clas = phylum+"|"+"c__unassigned"
    if len(entry) >= 10:
        order = clas+"|"+entry[8]
    else:
        order = clas+"|"+"o__unassigned"
    if len(entry) >= 12:
        family = order+"|"+entry[10]
    else:
        family = order+"|"+"f__unassigned"
    if len(entry) >= 14:
        genus = family+"|"+entry[12]
    else:
        genus = family+"|"+"g__unassigned"
    if len(entry) >= 16:
        species = genus+"|"+entry[14]
    else:
        species = genus+"|"+"s__unassigned"
    valist = [kingdom, phylum, clas, order, family, genus, species]
    for j in range(len(valist)):
        orfannotdic[orfname][taxlist[j]] = valist[j]      
        
#Write the GTF file
for i in orfdic:
    info = [orfdic[i]["con"],"Prodigal","ORF",orfdic[i]["s"],orfdic[i]["e"],".",orfdic[i]["d"],"."]
    inforow="\t".join(info)+'\tgene_id "{}";'.format(i)
    outfile.write(inforow)
    shortout.write(inforow[:-1]+"\n")
    featstr=""
    for j in annotlist:
        if j in orfannotdic[i]:
            fname=j.replace(" ","_")
            fval=orfannotdic[i][j].replace(";","_")
            fval=fval.replace("=","_")
            featstr+=' {} "{}";'.format(fname,fval)
    featstr=featstr[:-1]+"\n"
    outfile.write(featstr)

outfile.close()
shortout.close()
    
