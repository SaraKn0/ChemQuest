from flask import Flask, request, render_template
import uuid
from chemlib import Compound, Element
import chemlib.chemistry 
import random
import math
from chemlib.chemistry import pte

session = {}

#Charges for different elements 
charges = {"Ir" : 4,  1 : 1, 2: 2, 13 : 3, 15: 3, 
16 : 2, 17 : 1, 3 : 3, 4 : 4, 5 : 5, 6 : 6,  7 : 7,  8 : 4, 9 : 3,  10 : 2, 11 : 1, 12 : 2, 14 : 3
}

#All transition metals 
transitions = ["Ti", "V", "Nb", "Cr", "Mn", "Fe", "Ru", "Co", "Ni", "Pd", "Pt", "Cu", "Au", "Hg", "Tl",
"Sn", "Pb", "Sb", "Bi", "Po"]

#NAmes for anions 
anionname = {"O" : "Oxide", "N" : "Nitride", "P" : "Phosphide", "As" : "Arsenide", "S" : "Sulfide", "Se" : "Selenide", 
"Te" : "Telluride", "C" : "Carbide", "Si" : "Silicide"}

#Prefixes for molecular 
prefix = {1 : "mono", 2 : "di", 3 : "tri", 4 : "tetra", 5 : "penta", 6 : "hexa", 7 : "hepta", 8 : "octa", 9 : "nona", 10 : "deca"}

#Molecular compounds
molecular = ["SO2", "SO3", "NO2", "N2O4", "N2O5", "SF6", "N2O3", "Cl2O7", "P4O6", "PF5", "P4O10", "IF7",
"PCl5", "N2O", "CCl4", "NO", "N2O", "S2Cl2", "Cl2O7", "H2O", "CO", "CO2"]

#unicodes for subscripts - https://www.geeksforgeeks.org/how-to-print-superscript-and-subscript-in-python/
unicode = {2 : "\u2082", 3: "\u2083", 4: "\u2084", 5: "\u2085", 6: "\u2086", 7: "\u2087", 8: "\u2088", 9: "\u2089", 10: "\u2081\u2080"}



def create_compound():
    """
    Creates ionic compound, returns as string
    Returns:
        compoundold (str)
        namecomp (str)
        compound_type (str)
    """

    #Randomly choose between molecular or ionic - answer returned based on that

    #Add all elements from periodic table to list
    elements = list(pte.Symbol)
    cation = []
    anion = []
    nm = []
    nb = []
   
    #Create each element as an object - Element 
    for i in elements:
        element = Element(i)
        #If it is a noble gas, non reactive, add to noble gas list
        if element.Type == "Noble Gas":
            nb.append(element)
        #If metal, or less than 4 valence electrons add to cation list
        elif element.Valence < 4 or element.Type == "Metal":
            cation.append(element)
        #If more than 4 valence e's and not metalloid, add to anion
        elif element.Valence > 4 and element.Type != "Metalloid":
            anion.append(element)
        #Add rest to non metal list
        else:
            nm.append(element)
    #Radioactive elements, remove the lists since not necessary 
    remove = ["Nh", "Cn", "Rg", "Ds", "Mt", "Hs", "Bh", "Sg", "Db", "Rf", "Lv", "Ts", "Mc", "La", "Ac", "Ce", "Th", "Pr", "Pa",
              "Nd", "U", "Pm", "Np", "Sm", "Pu", "Eu", "Am", "Gd", "Cm", "Tb", "Bk", "Dy", "Cf", "Ho", "Es", "Er", "Fm",
              "Tm", "Md", "Yb", "No"]

    #For each value in remove
    for val in remove:
        #For each element in cation, if value matches element in list, remove from list
        for i in cation:
            if val == i.Symbol:
                cation.remove(i)
    #For each value in remove

    for val in remove:
        #For each element in anion, if value matches element in list, remove from list

        for i in anion:
            if val == i.Symbol:
                anion.remove(i) 

    #Generate a random number between 1 and 5
    
    x = random.randint(1,5)
   
    #If one, question will be a molecule 
    if x == 1:
        #Define type of compound 
        compound_type = "covalent"
        #Choose a random compound from list of molecules, convert to compound object
        compoundold = random.choice(molecular)
        compound = Compound(compoundold)
        els = []
        nums = []
        #Add each occurence into a list, add the number of occurences (how many of one element) to a list
        for i in compound.occurences:
            els.append(i)
            nums.append(compound.occurences[i])
        #First element in list relates to first element in compound
        el1 = Element(els[0])

        #For first element, if only one occurence, name is just element name
        if compound.occurences[el1.Symbol] == 1:
            name1 = el1.Element
        else:
            #For each element in occurences if it matches element in prefix, name is prefix + name of element 
            for i in prefix:
                if i == compound.occurences[el1.Symbol]:
                    name1 = prefix[i] + el1.Element.lower()

        #second element in list is second element in compound
        el2 = Element(els[1])
            
        #Access each element in prefix, what matches occurences for symbol is the prefix 
        for i in prefix:
            if i == compound.occurences[el2.Symbol]:
                pre = prefix[i]
            
        
        #If in anionname
        if el2.Symbol in anionname:
            #Access each element in anionname 
            for i in anionname:
                #If it matches element 2 symbol, name of element will be value of anionname at that symbol
                if i == el2.Symbol:
                    namean = anionname[i]
        #If not in anion name, remove last 3 characters from the elements' name and add ide 
        else:
            namean = el2.Element[:len(el2.Element)-3] + "ide"

        #If prefix is mono and element is oxide, the name should be monoxide instead of monooxide 
        if pre.lower() == "mono" and namean.lower() == "oxide":
            name2 = "monoxide"

        #If not, name of second element is prefix + anion name 
        else:

            name2 = pre + namean.lower()
        #Compound name is both names combined 
        namecomp = name1 + " " + name2

        #If there is one of first element and >1 of second element - formula is first element + second element + occurences as subscript 
        if nums[0] == 1 and nums[1] !=1:
            compoundold = els[0] + els[1] + unicode[nums[1]] #Access unicode at the index of the number of occurences 
        #One of  second element, >1 of first element, formula is first element + subscript of occurrences + second element
        elif nums[1] == 1 and nums[0] != 1:
            compoundold = els[0] + unicode[nums[0]] + els[1]
        #If one of both elements, compound name is both elements
        elif nums[1] == 1 and nums[0] == 1:
            compoundold = els[0] + els[1]
        #Both elements occur more than once, formula is first element + subscript of occurenves + second element + subscript of occurences
        else:
            compoundold = els[0] + unicode[nums[0]] + els[1] + unicode[nums[1]]
    #Any other number generated, ionic compound question 
    else:
        #Choose a random cation and anion from list 
        cat = random.choice(cation)
        an = random.choice(anion)
        chargecat = 0
        chargean = 0
        #If cation is a transition metal, randomly generate it's charge from it's possible options
        if cat.Symbol in transitions:
            compound_type = "transition"
            if cat.Symbol == "Ti" or cat.Symbol == "Ru":
                chargecat = random.choice([4,3])
            
            elif cat.Symbol == "V":
                chargecat = random.choice([5,4])

            elif cat.Symbol == "Nb" or cat.Symbol == "Sb" or cat.Symbol == "Bi":
                chargecat = random.choice([5,3])

            elif cat.Symbol == "Cr" or cat.Symbol == "Fe" or cat.Symbol == "Co" or cat.Symbol == "Ni":
                chargecat = random.choice([3,2])

            elif cat.Symbol == "Mn" or cat.Symbol == "Pd" or cat.Symbol == "Pt" or cat.Symbol == "Sn" or cat.Symbol == "Pb" or cat.Symbol == "Po":
                chargecat = random.choice([2,4])
            
        
            elif cat.Symbol == "Cu" or cat.Symbol == "Hg":
                chargecat = random.choice([2,1])

            elif cat.Symbol == "Au" or cat.Symbol == "Tl":
                chargecat = random.choice([3,1])
    
        #IF not transition - cation symbol in charges
        elif cat.Symbol in charges:
            compound_type = "ionic"
            for i in charges:
                if i == cat.Symbol:
                    chargecat = charges[i]
        #If cation symbol not in charges
        else:
            compound_type = "ionic"
            for i in charges:
                #Get cations group, what matches, store charge associated with that group
                if i == cat.Group:
                    chargecat = charges[i]
        #Anion charge based on group, accessed from charges dictionary 
        for i in charges:
            if i == an.Group:
                chargean = charges[i]
        
        #Find greatest common factor between the cations and anion charge 
        gcf = math.gcd(chargecat, chargean)
        #Divide each charge by gcf
        newchargecat = chargecat/gcf
        newchargean = chargean / gcf
        

        #If transition metal 
        if cat.Symbol in transitions:
            #Charge less than 3, cation name is element name + III for roman numeral 
            if chargecat <= 3:
                namecat = cat.Element + " " + "(" + ("I")*chargecat + ")"
            #Charge 4, cation name, roman numeral is IV
            elif chargecat == 4:
                namecat = cat.Element + " " + "(" + "IV" + ")"
            #If charge is 5, name is cation name,, roman numeral is V
            elif chargecat == 5:
                namecat = cat.Element + " " + "(" + "V" + ")"
            #Any other charge, name is element, roman numeral V, I for any remaining charge after 5
            else:
                namecat = cat.Element + " " + "(" + ("V") + ("I")*(chargecat-5) + ")"

        #If not transition, cation name is first letter capitalized, rest of the name of the element    
        else:
            namecat = (cat.Element[0]).upper() + cat.Element[1:]
                
        #For anions, check is symbol is in anionname
        if an.Symbol in anionname:
            #Find where it matches, anion name is value of anionname at symbol
            for i in anionname:
                if i == an.Symbol:
                    namean = anionname[i]
        #if not, remove last 3 letters of element name, add ide 
        else:
            namean = an.Element[:len(an.Element)-3] + "ide"

        #Final compound name cation name and anion name 
        namecomp = namecat + " " + namean

        #If both charges are one, formula is both elements 
        if newchargecat == 1 and newchargean == 1:
            compoundold = cat.Symbol + an.Symbol 
        #If only anion charge is 1, formula is cation + anion + subscript of cation charge
        elif newchargean == 1:
            compoundold = cat.Symbol  + an.Symbol + unicode[newchargecat]
        #If only cation charge is 1, formula is cation + anion charge subscript + anion
        elif newchargecat == 1:
            compoundold = cat.Symbol + unicode[newchargean] + an.Symbol 
        #If both charges >1, formula is cation + subscript of anion charge + anion + subscript cation charge
        else:
            compoundold =  cat.Symbol + unicode[newchargean] + an.Symbol + unicode[newchargecat]
     #Return string ompound, name of compound, type of compound
    return compoundold, namecomp, compound_type


def get_printable_compound():
    """
    Get compound, name of compound, type of compound
    Returns:
        compoundold (obj)
        namecomp (str)
        compound_type (str)
    """
    compoundold, namecomp, compound_type = create_compound()

    return compoundold, namecomp, compound_type

def validate_answer(answer, namecomp):
    """
    Validates user answer
    Args:
        answer (str)
        namecomp (str)
    Return:
        bool
    """

    #Return true if user answer matches correct answer, else false 
    return answer.lower() == namecomp.lower()

