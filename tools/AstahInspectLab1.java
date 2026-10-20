import java.util.Arrays;
import com.change_vision.jude.api.inf.AstahAPI;
import com.change_vision.jude.api.inf.model.*;
import com.change_vision.jude.api.inf.presentation.*;
import com.change_vision.jude.api.inf.project.ProjectAccessor;

/** Read the original Lab 1 model through the supported Astah API; never save it. */
class AstahInspectLab1 {
    /** Purpose: inspect conceptual/architectural continuity. Input: .asta path. Output: semantic audit on stdout. */
    public static void main(String[] args) throws Exception {
        ProjectAccessor project=AstahAPI.getAstahAPI().getProjectAccessor();
        try {
            project.open(args[0],true,false,true);
            System.out.println("ASTAH " + project.getAstahVersion());
            for (INamedElement element : project.findElements(IClass.class)) {
                IClass model=(IClass)element;
                System.out.println((model instanceof IComponent ? "COMPONENT " : "CLASS ") + model.getFullName("::") + " ABSTRACT="+model.isAbstract()+" STEREOTYPES="+Arrays.toString(model.getStereotypes())+" OWNER="+model.getOwner());
                System.out.println("DEFINITION " + model.getDefinition());
                for (IAttribute attribute : model.getAttributes()) if (attribute.getAssociation()==null) System.out.println("ATTRIBUTE "+attribute.getName()+":"+attribute.getTypeExpression());
                for (IOperation operation : model.getOperations()) System.out.println("OPERATION "+operation.getName());
                for (IPort port : model.getPorts()) {
                    System.out.println("PORT "+port.getName()+" TYPE="+port.getTypeExpression());
                    for (IClass iface : port.getProvidedInterfaces()) System.out.println("PROVIDES "+iface.getName());
                    for (IClass iface : port.getRequiredInterfaces()) System.out.println("REQUIRES "+iface.getName());
                }
            }
            for (INamedElement element : project.findElements(IAssociation.class)) {
                System.out.println("ASSOCIATION "+element.getName());
                for (IAttribute end : ((IAssociation)element).getMemberEnds()) System.out.println("END "+end.getType().getName()+" ROLE="+end.getName()+" MULTIPLICITY="+end.getMultiplicityRangeString()+" COMPOSITION="+end.isComposite()+" AGGREGATION="+end.isAggregate());
            }
            for (INamedElement element : project.findElements(IGeneralization.class)) {
                IGeneralization relation=(IGeneralization)element;
                System.out.println("GENERALIZATION "+relation.getSubType().getName()+" -> "+relation.getSuperType().getName());
            }
            for (INamedElement element : project.findElements(IDependency.class)) {
                IDependency relation=(IDependency)element;
                System.out.println("DEPENDENCY "+relation.getClient().getName()+" -> "+relation.getSupplier().getName()+" NAME="+relation.getName());
            }
            for (INamedElement element : project.findElements(IDiagram.class)) {
                IDiagram diagram=(IDiagram)element;
                System.out.println("DIAGRAM "+diagram.getName());
                for (IPresentation presentation : diagram.getPresentations()) if (presentation instanceof INodePresentation node) System.out.println("NODE "+node.getType()+" LABEL="+node.getLabel()+" MODEL="+node.getModel()+" PARENT="+node.getParent());
            }
        } finally { project.close(); }
        System.exit(0);
    }
}
