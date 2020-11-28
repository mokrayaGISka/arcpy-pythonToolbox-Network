import arcpy
arcpy.env.overwriteOutput = True

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Routes builder"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Routes builder"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0=arcpy.Parameter(
        	displayName="CSV-table",
        	name='input_table',
        	datatype='DETable',
        	parameterType='Required',
        	direction='Input',
        	multiValue=False)
        param1=arcpy.Parameter(
        	displayName="Output name",
        	name='output',
        	datatype='GPString',
        	parameterType='Required',
        	direction='Input',
        	multiValue=False)
        param2=arcpy.Parameter(
        	displayName="Railway",
        	name='railway',
        	datatype='DENetworkDataset',
        	parameterType='Required',
        	direction='Input',
        	multiValue=False)
        param3=arcpy.Parameter(
        	displayName="Restrictions",
        	name='restrictions',
        	datatype='DEShapeFile',
        	parameterType='Required',
        	direction='Input',
        	multiValue=False)
        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        input_table=parameters[0].value
        output=parameters[1].valueAsText
        network=parameters[2].value
        restrictions=parameters[3].value
        a=[]
        b=[]
        x0=[]
        y0=[]
        x1=[]
        y1=[]
        traffic = []
        for row in arcpy.da.SearchCursor(input_table, ["from", "to", "X1", "Y1", "X2", "Y2","traffic"]):
        	a.append(row[0].replace("-","_").replace(".","_").replace(" ","_").replace("(","").replace(")",""))
        	b.append(row[1].replace("-","_").replace(".","_").replace(" ","_").replace("(","").replace(")",""))
        	x0.append(row[2])
        	y0.append(row[3])
        	x1.append(row[4])
        	y1.append(row[5])
        	traffic.append(row[6])
        i = 0
        for x in range(len(a)):
        	route = a[x]+"__"+b[x]
        	arcpy.CreateFeatureclass_management("in_memory","temp", "POINT")
        	arcpy.AddField_management("in_memory/temp",'Name',"TEXT")
        	icurs=arcpy.da.InsertCursor("in_memory/temp",["SHAPE@XY", 'Name'])
        	icurs.insertRow([(y0[x],x0[x]), a[x]])
        	icurs.insertRow([(y1[x],x1[x]), b[x]])
        	arcpy.na.MakeRouteLayer(network,route,"Length")
        	routeLayer = arcpy.mapping.Layer(route)
        	fields = arcpy.ListFields("in_memory/temp")
        	fields1 = arcpy.ListFields(restrictions)
        	facilitiesSubLayerName = arcpy.na.GetNAClassNames(routeLayer)['Routes']
        	fieldMappings = arcpy.na.NAClassFieldMappings(routeLayer, 'Stops',False, fields)
        	restrictionsMappings = arcpy.na.NAClassFieldMappings(routeLayer, 'Point Barriers',False, fields1)
        	arcpy.na.AddLocations(route,"Stops","in_memory/temp",fieldMappings)
        	arcpy.na.AddLocations(route,"Point Barriers",restrictions,restrictionsMappings)
        	try:
				arcpy.na.Solve(route)
				arcpy.CopyFeatures_management(route+"/Routes",output+route)
				arcpy.AddField_management(output+route+".shp",'Traffic',"DOUBLE")
				ucurs=arcpy.da.UpdateCursor(output+route+".shp",["Traffic"])
				for row in ucurs:
					row[0] = traffic[x]
					ucurs.updateRow(row)
        	except:
        		arcpy.AddMessage('no solution found for route '+route)
        		with file(output + "unsolved.csv", 'a') as out:
                            out.write(a[x].encode("windows-1251")+";")
                            out.write(b[x].encode("windows-1251")+";")
                            out.write(str(x0[x])+";")
                            out.write(str(y0[x])+";")
                            out.write(str(x1[x])+";")
                            out.write(str(y1[x])+";")
                            out.write(str(traffic[x])+"\n")
        		i = i + 1
        	arcpy.Delete_management(route)
        	if x%50==0:
        		arcpy.AddMessage(str(x)+" Done")
        arcpy.AddMessage(str(i)+" unsolved in total")		
        arcpy.env.workspace = output	
        layers = arcpy.ListFeatureClasses()	
        arcpy.Merge_management(layers, output+"Routes")	
        for lyr in layers:
            arcpy.Delete_management(lyr)  