from graphviz import Digraph



class NFAState:

    def __init__(self):

        self.transitions = {}  # Dictionary: {symbol: [state1, state2, ...]}



class DFAState:

    def __init__(self, nfa_states):

        self.nfa_states = nfa_states  # Set of NFA states

        self.transitions = {}  # Dictionary: {symbol: DFAState}

        self.is_accept = False



class AutomatonConverter:

    def __init__(self, regex):

        self.regex = regex


    # Shunting Yard to convert infix regex to postfix

    def regex_to_postfix(self):

        precedence = {'*': 3, '.': 2, '+': 1}

        stack = []

        output = []

        

        # Explicitly handle concatenation

        modified_regex = self.insert_concatenation_operators(self.regex)


        for char in modified_regex:

            if char.isalnum():  # Operand

                output.append(char)

            elif char == '(':

                stack.append(char)

            elif char == ')':

                while stack and stack[-1] != '(':

                    output.append(stack.pop())

                stack.pop()

            else:  # Operator

                while stack and precedence.get(stack[-1], 0) >= precedence.get(char, 0):

                    output.append(stack.pop())

                stack.append(char)

        

        while stack:

            output.append(stack.pop())

        

        return ''.join(output)


    def insert_concatenation_operators(self, regex):

        """Insert explicit concatenation (.) operators for regex handling."""

        result = []

        for i in range(len(regex)):

            result.append(regex[i])

            if i + 1 < len(regex):

                # Check for cases where a concatenation operator is needed

                if (

                    regex[i].isalnum() or regex[i] == '*' or regex[i] == ')'

                ) and (

                    regex[i + 1].isalnum() or regex[i + 1] == '('

                ):

                    result.append('.')

        return ''.join(result)


    # Build the NFA from regex

    def construct_nfa(self, postfix):

        stack = []

        

        for char in postfix:

            if char.isalnum():  # Literal

                start = NFAState()

                accept = NFAState()

                start.transitions[char] = [accept]

                stack.append((start, accept))

            elif char == '*':  # Kleene Star

                nfa_start, nfa_accept = stack.pop()

                start = NFAState()

                accept = NFAState()

                start.transitions['ε'] = [nfa_start, accept]

                nfa_accept.transitions['ε'] = [nfa_start, accept]

                stack.append((start, accept))

            elif char == '.':  # Concatenation

                nfa2_start, nfa2_accept = stack.pop()

                nfa1_start, nfa1_accept = stack.pop()

                nfa1_accept.transitions['ε'] = [nfa2_start]

                stack.append((nfa1_start, nfa2_accept))

            elif char == '+':  # Union

                nfa2_start, nfa2_accept = stack.pop()

                nfa1_start, nfa1_accept = stack.pop()

                start = NFAState()

                accept = NFAState()

                start.transitions['ε'] = [nfa1_start, nfa2_start]

                nfa1_accept.transitions['ε'] = [accept]

                nfa2_accept.transitions['ε'] = [accept]

                stack.append((start, accept))

        

        return stack.pop()


    # Epsilon-closure computation

    def epsilon_closure(self, states):

        stack = list(states)

        closure = set(states)

        

        while stack:

            state = stack.pop()

            for next_state in state.transitions.get('ε', []):

                if next_state not in closure:

                    closure.add(next_state)

                    stack.append(next_state)

        

        return closure


    # Transition computation

    def move(self, states, symbol):

        next_states = set()

        for state in states:

            if symbol in state.transitions:

                next_states.update(state.transitions[symbol])

        return next_states


    # Convert NFA to DFA

    def nfa_to_dfa(self, nfa_start, nfa_accept):

        dfa_states = {}

        queue = []

        

        start_closure = frozenset(self.epsilon_closure([nfa_start]))

        dfa_start = DFAState(start_closure)

        dfa_start.is_accept = nfa_accept in start_closure

        dfa_states[start_closure] = dfa_start

        queue.append(dfa_start)


        # Add a dead state

        dead_state = DFAState(frozenset())

        for symbol in 'ab':  # Define all symbols for dead state

            dead_state.transitions[symbol] = dead_state


        # Add the dead state to the dfa_states

        dfa_states[frozenset()] = dead_state


        while queue:

            current_dfa_state = queue.pop(0)

            for symbol in set(char for state in current_dfa_state.nfa_states for char in state.transitions if char != 'ε'):

                move_result = self.move(current_dfa_state.nfa_states, symbol)

                closure = frozenset(self.epsilon_closure(move_result))

                

                if closure not in dfa_states:

                    new_dfa_state = DFAState(closure)

                    new_dfa_state.is_accept = nfa_accept in closure

                    dfa_states[closure] = new_dfa_state

                    queue.append(new_dfa_state)


                current_dfa_state.transitions[symbol] = dfa_states[closure]


            # Ensure every state has transitions for all possible input symbols (e.g., 'a', 'b')

            for symbol in 'ab':

                if symbol not in current_dfa_state.transitions:

                    current_dfa_state.transitions[symbol] = dead_state


        return dfa_start, dfa_states


    def regex_to_dfa(self):

        postfix = self.regex_to_postfix()

        nfa_start, nfa_accept = self.construct_nfa(postfix)

        return self.nfa_to_dfa(nfa_start, nfa_accept)


    def generate_dfa_diagram(self, dfa_start, dfa_states, output_file="dfa_diagram"):

        dot = Digraph(format="png")

        dot.attr(rankdir="LR")  # Left to right orientation


        state_names = {state: f"q{index}" for index, state in enumerate(dfa_states.values())}


        # Add nodes

        for dfa_state, name in state_names.items():

            shape = "doublecircle" if dfa_state.is_accept else "circle"

            dot.node(name, shape=shape)


        # Add transitions

        for dfa_state, name in state_names.items():

            for symbol, target_state in dfa_state.transitions.items():

                dot.edge(name, state_names[target_state], label=symbol)


        # Add the initial state arrow

        dot.node("start", shape="none", label="")

        dot.edge("start", state_names[dfa_start])


        dot.render(output_file, cleanup=True)

        print(f"DFA diagram saved as {output_file}.png!")



# Example Usage

regex = "(a+b+c)(a+b)*c"

converter = AutomatonConverter(regex)

dfa_start, dfa_states = converter.regex_to_dfa()

converter.generate_dfa_diagram(dfa_start, dfa_states, output_file="dfa_diagram")