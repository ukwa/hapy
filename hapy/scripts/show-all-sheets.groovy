//Groovy
mgr = appCtx.getBean("sheetOverlaysManager")

//review the associations
rawOut.println("------------------");
rawOut.println("SHEET ASSOCIATIONS");
rawOut.println("------------------\n");
mgr.sheetNamesBySurt.each{ k, v -> 
    rawOut.println("$k\n $v\n")
}

// List the sheets:
rawOut.println("------")
rawOut.println("SHEETS")
rawOut.println("------\n")
mgr.getSheetsByName().each{ name, sheet ->
    rawOut.println("$name")
    sheet.getMap().each{ k, v -> rawOut.println("$k = $v") }
    rawOut.println("")
}
