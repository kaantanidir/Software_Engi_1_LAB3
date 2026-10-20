import java.awt.geom.Point2D;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import com.change_vision.jude.api.inf.AstahAPI;
import com.change_vision.jude.api.inf.editor.*;
import com.change_vision.jude.api.inf.model.*;
import com.change_vision.jude.api.inf.presentation.*;
import com.change_vision.jude.api.inf.project.ProjectAccessor;

/** Repair a copy through Astah's supported model/presentation API. */
class AstahRepair {
    /** Input: source, optional destination and TSV. Output: saved .asta and semantic audit. */
    public static void main(String[] args) throws Exception {
        ProjectAccessor project = AstahAPI.getAstahAPI().getProjectAccessor();
        try {
            project.open(args[0], true, false, true);
            if (args.length > 1) repair(project, args[1], args[2]);
            audit(project);
        } finally { project.close(); }
        System.exit(0);
    }

    /** Input: accessor/path/TSV. Output: corrected diagram and descriptions, saved apart from baseline. */
    static void repair(ProjectAccessor project, String output, String tsv) throws Exception {
        BasicModelEditor basic = project.getModelEditorFactory().getBasicModelEditor();
        UseCaseModelEditor cases = project.getModelEditorFactory().getUseCaseModelEditor();
        UseCaseDiagramEditor editor = project.getDiagramEditorFactory().getUseCaseDiagramEditor();
        TransactionManager.beginTransaction();
        try {
            Map<String,IUseCase> models = new LinkedHashMap<>();
            for (INamedElement element : project.findElements(IUseCase.class)) {
                IUseCase useCase = (IUseCase) element;
                useCase.setName(useCase.getName().strip());
                models.put(useCase.getName(), useCase);
            }
            String[] fields = {"Preconditions", "InitiatingActor", "Goal", "MainScenario", "Alternatives"};
            for (String line : Files.readAllLines(Path.of(tsv), StandardCharsets.UTF_8)) {
                String[] values = line.split("\t", -1);
                IUseCase useCase = models.get(values[0]);
                StringBuilder definition = new StringBuilder("Name: " + values[0] + "\n");
                for (int i=0; i<fields.length; i++) {
                    String value = new String(Base64.getDecoder().decode(values[i+1]), StandardCharsets.UTF_8);
                    String key = "uc.description." + fields[i];
                    boolean found=false;
                    for (ITaggedValue tag : useCase.getTaggedValues()) if (tag.getKey().equals(key)) { tag.setValue(value); found=true; }
                    if (!found) basic.createTaggedValue(useCase, key, value);
                    definition.append(fields[i]).append(": ").append(value).append("\n");
                }
                useCase.setDefinition(definition.toString());
            }
            for (INamedElement element : project.findElements(IDiagram.class)) editor.delete((IDiagram)element);
            for (INamedElement element : project.findElements(IAssociation.class)) basic.delete(element);
            for (INamedElement element : project.findElements(IInclude.class)) basic.delete(element);
            for (INamedElement element : project.findElements(IExtend.class)) basic.delete(element);
            editor.createUseCaseDiagram(project.getProject(), "SmartBrew AI - corrected use cases");
            editor.createRect(new Point2D.Double(210,20),1080,1140);
            editor.createText("SmartBrew AI",new Point2D.Double(235,35));
            Map<String,INodePresentation> nodes=new LinkedHashMap<>();
            String[] names={"Browse Menu and Nutrition","Log In","Create / Manage Profile","Customize Beverage","Process Natural Language Order","Check Ingredient Availability","Generate Recommendations","Analyze Mood","Process Payment","Redeem Loyalty","Receive Receipt","Manage Inventory","View Error Logs"};
            double[][] geometry={{300,100,300},{300,210,300},{300,320,300},{300,430,300},{850,430,340},{850,530,340},{300,620,300},{850,620,340},{300,770,300},{850,770,340},{300,880,300},{300,990,300},{850,990,340}};
            for (int i=0;i<names.length;i++) {
                INodePresentation node=editor.createNodePresentation(models.get(names[i]),new Point2D.Double(geometry[i][0],geometry[i][1]));
                node.setWidth(geometry[i][2]);node.setHeight(60);nodes.put(names[i],node);
            }
            Map<String,IClass> actors=new HashMap<>();
            for (INamedElement element : project.findElements(IClass.class)) if (element.hasStereotype("actor")) actors.put(element.getName(),(IClass)element);
            String[] actorNames={"Customer","Technician","Payment Processor"};
            double[][] actorPositions={{30,390},{30,1000},{1380,790}};
            for (int i=0;i<actorNames.length;i++) nodes.put(actorNames[i],editor.createNodePresentation(actors.get(actorNames[i]),new Point2D.Double(actorPositions[i][0],actorPositions[i][1])));
            for (String name : List.of("Browse Menu and Nutrition","Log In","Create / Manage Profile","Customize Beverage","Generate Recommendations","Process Payment","Receive Receipt")) association(basic,editor,actors.get("Customer"),models.get(name),nodes.get("Customer"),nodes.get(name));
            for (String name : List.of("Manage Inventory","View Error Logs")) association(basic,editor,actors.get("Technician"),models.get(name),nodes.get("Technician"),nodes.get(name));
            association(basic,editor,actors.get("Payment Processor"),models.get("Process Payment"),nodes.get("Payment Processor"),nodes.get("Process Payment"));
            IInclude include=cases.createInclude(models.get("Customize Beverage"),models.get("Check Ingredient Availability"),"");
            if (!include.getIncludingCase().getName().equals("Customize Beverage")) throw new IllegalStateException("Include direction mismatch");
            editor.createLinkPresentation(include,nodes.get("Check Ingredient Availability"),nodes.get("Customize Beverage"));
            extend(cases,editor,models,nodes,"Process Natural Language Order","Customize Beverage","natural-language entry");
            extend(cases,editor,models,nodes,"Analyze Mood","Generate Recommendations","optional mood context");
            extend(cases,editor,models,nodes,"Redeem Loyalty","Process Payment","loyalty redemption");
            INodePresentation note=editor.createNote("Group feature: Loyalty Point Redemption",new Point2D.Double(850,880));
            editor.createNoteAnchor(note,nodes.get("Redeem Loyalty"));
            TransactionManager.endTransaction();
            project.validateProject();
            project.saveAs(output);
        } catch (Exception error) { TransactionManager.abortTransaction(); throw error; }
    }

    /** Input: actor/use case and presentations. Output: solid participation link. */
    static void association(BasicModelEditor basic,UseCaseDiagramEditor editor,IClass actor,IUseCase useCase,INodePresentation a,INodePresentation u) throws Exception {
        IAssociation relation=basic.createAssociation(actor,useCase,"","","");
        ILinkPresentation link=editor.createLinkPresentation(relation,a,u);
        double ay=a.getLocation().getY()+a.getHeight()/2;
        double uy=u.getLocation().getY()+u.getHeight()/2;
        if (actor.getName().equals("Customer")) {
            link.setAllPoints(new Point2D[]{new Point2D.Double(70,ay),new Point2D.Double(170,ay),new Point2D.Double(170,uy),new Point2D.Double(u.getLocation().getX(),uy)});
        } else if (actor.getName().equals("Technician") && useCase.getName().equals("View Error Logs")) {
            link.setAllPoints(new Point2D[]{new Point2D.Double(70,ay),new Point2D.Double(170,ay),new Point2D.Double(170,1100),new Point2D.Double(800,1100),new Point2D.Double(850,uy)});
        } else if (actor.getName().equals("Payment Processor")) {
            link.setAllPoints(new Point2D[]{new Point2D.Double(1380,ay),new Point2D.Double(1320,ay),new Point2D.Double(1320,860),new Point2D.Double(650,860),new Point2D.Double(600,uy)});
        }
    }

    /** Input: optional extension/base/point. Output: extend relationship directed to the base. */
    static void extend(UseCaseModelEditor cases,UseCaseDiagramEditor editor,Map<String,IUseCase> models,Map<String,INodePresentation> nodes,String extension,String base,String point) throws Exception {
        IExtend relation=cases.createExtend(models.get(extension),models.get(base),"");
        if (!relation.getExtension().getName().equals(extension)) throw new IllegalStateException("Extend direction mismatch");
        cases.createExtensionPoint(models.get(base),point);
            editor.createLinkPresentation(relation,nodes.get(base),nodes.get(extension));
    }

    /** Input: saved accessor. Output: relationship/description completeness audit on stdout. */
    static void audit(ProjectAccessor project) throws Exception {
        System.out.println("ASTAH " + project.getAstahVersion());
        for (INamedElement element : project.findElements(IUseCase.class)) {
            IUseCase useCase=(IUseCase)element;
            System.out.println("USECASE " + useCase.getName());
            for (String key : List.of("Preconditions","InitiatingActor","Goal","MainScenario","Alternatives")) {
                String text=useCase.getTaggedValue("uc.description."+key);
                System.out.println("FIELD " + key + " " + (text == null ? 0 : text.length()));
            }
        }
        for (INamedElement element : project.findElements(IInclude.class)) {
            IInclude relation=(IInclude)element;
            System.out.println("INCLUDE " + relation.getIncludingCase().getName() + " -> " + relation.getAddition().getName());
        }
        for (INamedElement element : project.findElements(IExtend.class)) {
            IExtend relation=(IExtend)element;
            System.out.println("EXTEND " + relation.getExtension().getName() + " -> " + relation.getExtendedCase().getName());
        }
    }
}
