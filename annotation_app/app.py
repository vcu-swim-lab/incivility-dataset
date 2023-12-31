import argparse
import streamlit as st
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from database import Database
import configparser

# Read configuration from the file
config = configparser.ConfigParser()
config.read('config.ini')

db = Database(config['Files']['db_path'])

df_comments = pd.read_csv(config['Files']['comments'])
df_issues = pd.read_csv(config['Files']['issues'])

tbdfs = [
    '', 'None', 'Bitter frustration', 'Impatience', 'Irony', 'Insulting', 'Mocking', 'Threat', 'Vulgarity',
    'Entitlement', 'Identity attacks/Name-Calling'
]
triggers = [
    '', 'None', 'Failed use of tool/code or error messages', 'Communication breakdown', 'Rejection',
    'Violation of community conventions', 'Past interactions', 'Politics/ideology', 'Technical disagreement',
    'Unprovoked'
]
targets = [
    '', 'None', 'Code/tool', 'People', 'Company/organization', 'Self-directed', 'Undirected'
]
consequences = [
    '', 'None', 'Invoke Code of Conduct', 'Escalating further', 'Discontinued further discussion',
    'Provided technical explanation', 'Accepting criticism', 'Trying to stop the incivility'
]


@dataclass
class AnnotatedComment:
    comment_id: int
    issue_id: int
    user_id: int
    created_at: str
    comment_body: str
    annotation = "None"
    annotation_other = ""

def next():
    st.session_state.counter += 1
    st.session_state.issue_level = 1


def insert_comment(issue_id, comment_id, user_login, tbdf):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"{current_time}, {issue_id}, {comment_id}, {user_login}, {tbdf}")

    if st.session_state.disable_counter < len(st.session_state.tbdf_selection_done):
        st.session_state.tbdf_selection_done[st.session_state.disable_counter] = True
    st.session_state.disable_counter += 1
    st.session_state.counter += 1
    st.session_state.issue_level = 1

    db.insert_comment_annotation(issue_id, comment_id, tbdf)


def next_issue(user_login, issue_id, trigger, target, consequences, additional_comments):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"{current_time}, {issue_id}, {user_login}, {trigger}, {target}, {consequences}, {additional_comments}")

    st.session_state.counter += 1
    st.session_state.issue_level = 1
    st.session_state.comments_on_screen = []
    st.session_state.tbdf_selection_done = []

    db.insert_issue_annotation(issue_id, trigger, target, consequences, additional_comments)
    current_annotation_id = db.currently_annotating(st.session_state.user_login)[0]
    db.current_issue_done(current_annotation_id)
    db.update_annotation_count(user_login)

    js = '''<script>
                var body = window.parent.document.querySelector(".main");
                console.log(body);
                body.scrollTop = 0;
            </script>
        '''

    st.components.v1.html(js)

def finish_annotation(user_login, issue_id, trigger, target, consequences, additional_comments):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"{current_time}, {issue_id}, {user_login}, {trigger}, {target}, {consequences}, {additional_comments}")

    st.session_state.counter += 1
    st.session_state.issue_level = 1
    st.session_state.comments_on_screen = []
    st.session_state.tbdf_selection_done = []
    
    db.insert_issue_annotation(issue_id, trigger, target, consequences, additional_comments)
  
    current_annotation_id = db.currently_annotating(st.session_state.user_login)[0]
    # print(current_annotation_id)
    db.current_issue_done(current_annotation_id)
    db.update_annotation_count(user_login)

    end_annotation(st.session_state.user_login)

    st.session_state.annotation_finished = 1


# def finish_annotation():
#     st.session_state.annotation_finished = 1


def next_issue_level(issue_id, comment_id, user_login, tbdf):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"{current_time}, {issue_id}, {comment_id}, {user_login}, {tbdf}")

    db.insert_comment_annotation(issue_id, comment_id, tbdf)

    if st.session_state.disable_counter < len(st.session_state.tbdf_selection_done):
        st.session_state.tbdf_selection_done[st.session_state.disable_counter] = True

    st.session_state.disable_counter += 1

    st.session_state.issue_level = 0
    st.session_state.disable_counter = 0

def end_annotation(user):
    # print(user)
    db.update_wrap_annotaion(user)

def prev():
    if st.session_state.counter != 0:
        st.session_state.counter -= 1


def st_on_change(comment, option):
    comment.annotation = option


if 'counter' not in st.session_state: st.session_state.counter = 0

if 'disable_counter' not in st.session_state: st.session_state.disable_counter = 0

if 'annotation_finished' not in st.session_state: st.session_state.annotation_finished = 0

if 'logged_in' not in st.session_state: st.session_state.logged_in = 0

if 'user_login' not in st.session_state: st.session_state.user_login = ''

if 'issue_level' not in st.session_state: st.session_state.issue_level = 1

if "issue_id" not in st.session_state:
    st.session_state.issue_id = 0

if "comments_on_screen" not in st.session_state:
    comments_on_screen = []
    st.session_state.comments_on_screen = comments_on_screen
else:
    comments_on_screen = st.session_state.comments_on_screen

if "tbdf_selection_done" not in st.session_state:
    tbdf_selection_done = []
    st.session_state.tbdf_selection_done = tbdf_selection_done
else:
    tbdf_selection_done = st.session_state.tbdf_selection_done

# Load comment and the current annotations
if "my_comments" not in st.session_state:
    comments = df_comments.to_dict(orient='records')
    my_comments = [AnnotatedComment(comment_id=comments[i].get('comment_id'),
                                    issue_id=comments[i].get('issue_id'),
                                    comment_body=comments[i].get('comment_body'),
                                    user_id=comments[i].get('user_id'),
                                    created_at=comments[i].get('created_at')
                                    ) for i in range(len(comments))]
    st.session_state.my_comments = my_comments
else:
    my_comments = st.session_state.my_comments


def inject_css():
    s = f"""
        <style>
        blockquote {{background-color: #dfdfe1; border-radius: 5px}}
        <style>
        """
    st.markdown(s, unsafe_allow_html=True)


def instructions():
    with open(config['Files']['instructions'], 'r') as file:
        file_content = file.read()

    return f'''{file_content}'''

def main():
    st.set_page_config(layout="wide")
    inject_css()
    # print("logged in state: ", st.session_state.logged_in)
    logged_in = st.session_state.logged_in
    user_login = ''
    if not logged_in:
        with st.form("my_form"):
            st.write("Please login with the provided login info")
            user_login = st.text_input('User Login')
            submitted = st.form_submit_button("Submit")
            if submitted:
                user = db.get_user(user_login)
                if user is None:
                    st.toast('User not found!')
                else:
                    if st.session_state.logged_in == 0:
                        current_time = datetime.now().strftime("%H:%M:%S")
                        print(f"{user_login} Logged in at time: {current_time}")
                        st.session_state.counter = 0
                        st.session_state.disable_counter = 0
                        st.session_state.issue_id = 0
                    st.session_state.logged_in = 1
                    st.session_state.user_login = user_login
                    is_admin = user.get('is_admin')
                    if is_admin == 2:
                        st.session_state.annotation_finished = 1
                        st.rerun()
                    elif is_admin == 0:
                        logged_in = 1
                        st.rerun()
                    elif is_admin == 1:
                        logged_in = 1
                        st.rerun()

    elif st.session_state.user_login == 'db_admin':
        with open("annotation.db", "rb") as fp:
            btn = st.download_button(
                label="Download db file",
                data=fp,
                file_name="annotation.db",
                mime="application/octet-stream"
            )


        all_users_annotation_count = db.get_annotation_count()
        all_users_annotation_count = pd.DataFrame(all_users_annotation_count)
        st.subheader('User Annotaiton Count')
        st.table(all_users_annotation_count)


        st.subheader('Input Select SQL:')
        # Use st.form to create a form
        with st.form("sql_form"):
            # Add form components
            sql = st.text_input("Input Select SQL:", max_chars=1000)
            submitted = st.form_submit_button("Submit SQL")
        if submitted:
            sql = sql.strip().lower()
            if sql.startswith("select"):
                try:
                    results = db.select(sql)
                    st.table(results)
                except Exception as e:
                    st.success(f"Error with query: {sql}, Exception: {e}")
            else:
                st.success(f"Not a select query: {sql}")

        all_issues = db.get_all_annotated_issues()
        all_issues = pd.DataFrame(all_issues[0], columns=all_issues[1])
        csv_data = all_issues.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download annodated issues",
            data=csv_data,
            file_name='annotated_issues.csv',
            # key='download_button_issues'
        )

        all_comments= db.get_all_annotated_comments()
        all_comments = pd.DataFrame(all_comments[0], columns=all_comments[1])
        # filtered_df = df_comments[['comment_id', 'comment_body']]
        # merged_df = pd.merge(all_comments, filtered_df, on='comment_id', how='left')
        csv_data_comments = all_comments.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download annodated comments",
            data=csv_data_comments,
            file_name='annotated_comments.csv',
        )

        with st.form("Comments on This Issue:"):
            issue_id = st.text_input("Input Issue Id:", max_chars=20)
            comments_submitted = st.form_submit_button("Comments on This Issue")
        if comments_submitted:
            try:
                column_to_filter = 'issue_id'
                target_value = int(issue_id)
                filtered_rows = all_comments[all_comments[column_to_filter] == target_value]
                st.table(filtered_rows)
            except:
                st.success(f"Error with Issue Id: {issue_id}")


        with st.form("Annotated Comment:"):
            comment_id = st.text_input("Input Comment Id:", max_chars=20)
            comments_submitted = st.form_submit_button("Annotated Comment")
        if comments_submitted:
            try:
                column_to_filter = 'comment_id'
                target_value = int(comment_id)
                filtered_rows = all_comments[all_comments[column_to_filter] == target_value]
                st.table(filtered_rows)
            except:
                st.success(f"Error with Comment Id: {comment_id}")


        st.subheader('Annotated Issues')
        st.table(all_issues)


        # st.subheader('All Comments')
        # st.table(merged_df)

    else:
        if st.session_state.annotation_finished:
            st.empty()
            st.markdown('# Annotations Completed! Thanks for your participation!')
            st.balloons()

        else:
            if db.currently_annotating(st.session_state.user_login) == None:
                next_available_issue_id = db.get_next_avaiable_issue()
                print(f"next_available_issue_id: {next_available_issue_id}")
                if next_available_issue_id != None:
                    next_available_issue_id = next_available_issue_id[0]
                    db.assigning_next_avaiable_issue(st.session_state.user_login, next_available_issue_id)
                else:
                    print("Assigning an old issue!")
                    db.assigning_an_old_issue(st.session_state.user_login)

            currently_annotating_issue_id = db.currently_annotating(st.session_state.user_login)
            if currently_annotating_issue_id == None:
                print(f"currently_annotating_issue_id is None")
            else:
                currently_annotating_issue_id = currently_annotating_issue_id[0]
                # print(f"currently_annotating_issue_id: {currently_annotating_issue_id}")

            # print("current issue:", currently_annotating_issue_id)
            st.session_state.issue_id = currently_annotating_issue_id
            while True:
                comment = my_comments[st.session_state.counter % (len(my_comments))]
                if comment.issue_id != currently_annotating_issue_id:
                    next()
                else:
                    break
            next_comment = my_comments[(st.session_state.counter + 1) % (len(my_comments))]

            issues = df_issues.to_dict(orient='records')
            issue_titles = {}
            for issue in issues:
                issue_titles[issue.get('issue_id')] = issue.get('issue_title')

            st.write("""
                     # Issue {}
                     ## {}
                     """.format(st.session_state.issue_id, issue_titles[st.session_state.issue_id]))
            cols = st.columns([3, 1])

            # with cols[0]:
            n = 0
            if comment not in st.session_state.comments_on_screen:
                st.session_state.comments_on_screen.append(comment)
                st.session_state.tbdf_selection_done.append(False)

            with st.sidebar:
                
                annotated = db.get_number_of_issues_annotated_by_user(st.session_state.user_login)

                progress_text = f"Number of issues annotated: {annotated}\n\n Number of issues remaining: {20 - annotated}"
                progress_text = progress_text + "\n\n Comments remaining in this issue"

                total_comments_counter = (df_comments['issue_id'] == st.session_state.issue_id).sum()
                if total_comments_counter > 0:
                    my_bar = st.progress(0, text=progress_text)
                    percent = (len(st.session_state.comments_on_screen)) / total_comments_counter
                    if percent == 1:
                        progress_text = "Comments completed!"
                    else:
                        my_bar.progress((len(st.session_state.comments_on_screen)) / total_comments_counter, progress_text)
                st.write(instructions())

            for comment, tbdf_option_disabled in zip(st.session_state.comments_on_screen, st.session_state.tbdf_selection_done):
                with st.chat_message("user"):
                    datetime_object = datetime.strptime(comment.created_at, '%Y-%m-%dT%H:%M:%SZ')
                    metadata = """
                                ##### User {}
                                {},     **Comment {}**
                            """.format(comment.user_id, datetime_object, str(n))
                    st.write(metadata)
                    comment_body = str(comment.comment_body)
                    comment_body = comment_body.replace("```", '').replace("##", '')
                    st.write(comment_body)
                    st.markdown('---')
                    option = st.selectbox(label='Select TBDF', options=tbdfs, key=comment.comment_id, index=0, disabled=tbdf_option_disabled)
                    comment.annotation = option

                    n += 1

            if next_comment.issue_id != st.session_state.issue_id:
                if st.session_state.issue_level == 1:
                    comment_id = comment.comment_id
                    comment_annotation = comment.annotation
                    option_disabled1 = True
                    if comment_annotation == '':
                        option_disabled1 = True
                    else:
                        option_disabled1 = False
                    st.button("Issue level ➡️", disabled=option_disabled1, on_click=next_issue_level, use_container_width=True, args=(currently_annotating_issue_id,
                                                                                                                                comment_id,
                                                                                                                                st.session_state.user_login,
                                                                                                                                comment_annotation))
                primary_color = st.get_option("theme.primaryColor")
                s = f"""
                <style>
                div.stButton > button:first-child {{ border: 5px solid {primary_color}; background-color: #FF4081; color: white;}}
                blockquote {{background-color: #dfdfe1; border-radius: 5px}}
                <style>
                """
                st.markdown(s, unsafe_allow_html=True)
            else:
                comment_id = comment.comment_id
                comment_annotation = comment.annotation
                if comment_annotation == '':
                    option_disabled = True
                else:
                    option_disabled = False

                st.button("Next Comment ⬇️", disabled=option_disabled, on_click=insert_comment, use_container_width=True, args=(currently_annotating_issue_id, 
                                                                                                                                comment_id, 
                                                                                                                                st.session_state.user_login, 
                                                                                                                                comment_annotation))

            if not st.session_state.issue_level:
                next_issue_disabled = True
                st.info('Please indicate the trigger, target, and consequences')

                option_trigger = st.selectbox(
                    'Trigger',
                    triggers,
                    disabled=st.session_state.issue_level,
                    key='option_trigger' + str(st.session_state.issue_id))
                option_target = st.selectbox(
                    'Target',
                    targets,
                    disabled=st.session_state.issue_level,
                    key='option_target' + str(st.session_state.issue_id))
                option_consequences = st.multiselect(
                    'Consequences',
                    consequences,
                    disabled=st.session_state.issue_level,
                    key='option_consequences' + str(st.session_state.issue_id))
                additional_comments = st.text_input('Additional Comments', key='additional_comments' + str(st.session_state.issue_id))
                if st.session_state.issue_level == 0:
                    total_annotated_issues = db.get_number_of_issues_annotated_by_user(st.session_state.user_login)
                    # print(f"total_annotated_issues: {total_annotated_issues}")
                    if total_annotated_issues < 19:
                        if str(option_trigger) != '' and str(option_target) != '' and option_consequences != []:
                            next_issue_disabled = False
                        st.button("Next Issue ✅", disabled=next_issue_disabled,
                                  on_click=next_issue, use_container_width=True,
                                  args=(st.session_state.user_login, comment.issue_id, option_trigger, str(option_target), str(option_consequences), additional_comments))
                    else:
                        if str(option_trigger) != '' and str(option_target) != '' and option_consequences != []:
                            next_issue_disabled = False
                        st.button("Finish Annotation ✅", disabled=next_issue_disabled,
                                  on_click=finish_annotation, use_container_width=True,
                                  args=(st.session_state.user_login, comment.issue_id, option_trigger, str(option_target), str(option_consequences), additional_comments))


if __name__ == "__main__":
    main()
